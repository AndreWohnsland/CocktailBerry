"""Wi-Fi uplink on wlan0, shared by the Qt app and the API.

The access point on wlan1 is the tablet's fixed address and the uplink only gives the machine
internet, so a join is kept only when the access point is active again afterwards. Anything else
is rolled back: the new profile is deleted so NetworkManager stops retrying it on its own, which
would keep kicking the access point off the shared radio.
"""

import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Literal

from src.connection import access_point
from src.connection.access_point import _UP_WAIT, parse_nmcli_terse, run_privileged
from src.logger_handler import LoggerHandler

STA_IFACE = "wlan0"
_JOIN_WAIT = 60

_logger = LoggerHandler("wifi")


@dataclass
class JoinResult:
    success: bool
    ssid: str
    reason: str = ""  # last nmcli stderr line on failure


@dataclass
class Connection:
    profile: str | None  # NetworkManager names it after the SSID, uniquified, or e.g. "preconfigured"
    ssid: str | None
    ip: str | None


def list_available_ssids() -> list[str]:
    try:
        result = run_privileged("nmcli", "-t", "-f", "SSID", "dev", "wifi", "list", "ifname", STA_IFACE)
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        _logger.error(f"Failed to list available WiFi networks: {e}")
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def current_connection() -> Connection:
    try:
        result = run_privileged(
            "nmcli", "-t", "-f", "GENERAL.CONNECTION,IP4.ADDRESS", "dev", "show", STA_IFACE, check=False
        )  # fmt: skip
    except (subprocess.SubprocessError, FileNotFoundError):
        return Connection(None, None, None)
    if result.returncode != 0:
        return Connection(None, None, None)
    fields = parse_nmcli_terse(result.stdout)
    profile = fields.get("GENERAL.CONNECTION") or None
    ip = fields.get("IP4.ADDRESS[1]", "").split("/")[0] or None
    return Connection(profile, _profile_field(profile, "802-11-wireless.ssid") if profile else None, ip)


def join(ssid: str, password: str) -> JoinResult:
    """Join the network; on any failure restore the previous uplink and the access point."""
    ap_before = access_point.read_ap()
    previous = current_connection().profile
    # `dev wifi connect` reuses a profile for that SSID and overwrites its password, so keep the
    # old one: the typical failure is retyping the current uplink with a typo
    previous_psk = _profile_field(previous, "802-11-wireless-security.psk") if previous else None
    profiles_before = _profile_uuids()
    try:
        result = run_privileged(
            "nmcli", "--wait", str(_JOIN_WAIT), "dev", "wifi", "connect", ssid, "password", password,
            "ifname", STA_IFACE, check=False, timeout=_JOIN_WAIT + 10,
        )  # fmt: skip
        reason = _last_line(result.stderr) if result.returncode != 0 else _restore_access_point(ap_before)
    except (OSError, subprocess.SubprocessError) as e:
        reason = _last_line(getattr(e, "stderr", None)) or str(e)
    if not reason:
        _logger.info(f"Joined '{ssid}'")
        return JoinResult(True, ssid)
    _logger.error(f"Joining '{ssid}' failed, rolling back: {reason}")
    _rollback(_profile_uuids() - profiles_before, previous, previous_psk, ap_before)
    return JoinResult(False, ssid, reason)


def _restore_access_point(ap_before: access_point.ApStatus) -> str:
    """Return an empty string when the access point is where it was, else why it is not."""
    if not ap_before.enabled:
        return ""
    # the dispatcher and NetworkManager's autoconnect usually bring it back on their own; a `con up`
    # on an AP that is active or activating would restart it and kick every client
    for attempt in range(4):
        if attempt:
            time.sleep(2)
        if access_point.read_ap().enabled:
            return ""
    try:
        access_point.activate()
    except subprocess.CalledProcessError as e:
        return _last_line(e.stderr) or "access point did not come back"
    return ""


def _rollback(
    new_profiles: set[str], previous: str | None, previous_psk: str | None, ap_before: access_point.ApStatus
) -> None:
    for uuid in new_profiles:
        run_privileged("nmcli", "connection", "delete", uuid, check=False)
    if previous:
        if previous_psk:
            run_privileged("nmcli", "connection", "modify", previous, "wifi-sec.psk", previous_psk, check=False)
        run_privileged("nmcli", "--wait", str(_UP_WAIT), "connection", "up", previous, check=False)
    if ap_before.enabled and not access_point.read_ap().enabled:
        try:
            access_point.activate()
        except subprocess.SubprocessError:
            _logger.error("Access point could not be restored after rollback, the dispatcher keeps trying")


def _profile_field(profile: str, field: str) -> str | None:
    result = run_privileged("nmcli", "-s", "-g", field, "connection", "show", profile, check=False)
    return result.stdout.strip() or None if result.returncode == 0 else None


def _profile_uuids() -> set[str]:
    result = run_privileged("nmcli", "-t", "-f", "UUID", "connection", "show", check=False)
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _last_line(text: str | None) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[-1] if lines else ""


@dataclass(frozen=True)
class JoinJob:
    state: Literal["idle", "running", "succeeded", "failed"]
    ssid: str = ""
    reason: str = ""


class JoinRunner:
    """One background join at a time for the API.

    The request returns at once because the tablet sits on the access point, which may blink while
    the radio switches channel; a request spanning the join would break mid-flight.
    """

    def __init__(self) -> None:
        self._job = JoinJob("idle")
        self._lock = threading.Lock()

    def start(self, ssid: str, password: str) -> bool:
        """Start the join in the background, False when one is already running."""
        with self._lock:
            if self._job.state == "running":
                return False
            self._job = JoinJob("running", ssid)
        threading.Thread(target=self._run, args=(ssid, password), daemon=True).start()
        return True

    def _run(self, ssid: str, password: str) -> None:
        try:
            result = join(ssid, password)
        except Exception as e:  # a stuck "running" would block every later join
            _logger.log_exception(e)
            result = JoinResult(False, ssid, str(e))
        with self._lock:
            self._job = JoinJob("succeeded" if result.success else "failed", ssid, result.reason)

    @property
    def job(self) -> JoinJob:
        with self._lock:
            return self._job


JOIN_RUNNER = JoinRunner()
