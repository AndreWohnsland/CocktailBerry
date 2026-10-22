"""Access point lifecycle, shared by the CLI, the Qt app and the API.

NetworkManager is the persistent store: the profile under CONNECTION_NAME survives
project resets and carries SSID, password and autoconnect (= enabled) state.
"""

import io
import subprocess
import time
from dataclasses import dataclass

import qrcode

from src.logger_handler import LoggerHandler

CONNECTION_NAME = "CocktailBerry-AP"
DEFAULT_SSID = "CocktailBerry"
DEFAULT_PASSWORD = "cocktailconnect"
AP_ADDRESS = "10.42.0.1"
SSID_LENGTH = (1, 32)
PASSWORD_LENGTH = (8, 63)  # WPA2 PSK bounds
_TIMEOUT = 30
# nmcli waits for an activation itself; keep that below the subprocess timeout so a slow
# NetworkManager yields an nmcli error line instead of a killed process
_UP_WAIT = 25
# NetworkManager blocks a profile after a few failed activations; the AP must keep trying forever,
# otherwise a flapping uplink on the shared radio leaves it off until the next reboot
_AUTOCONNECT_RETRIES = ("connection.autoconnect-retries", "0")

_logger = LoggerHandler("access_point")

_AP_IFACE_UNIT_PATH = "/etc/systemd/system/cocktailberry-ap-iface.service"
# iw only creates the AP interface at runtime, so after a reboot wlan1 is gone and the AP
# profile has no device to autoconnect to. Recreate it on every boot.
_AP_IFACE_UNIT = """[Unit]
Description=CocktailBerry AP virtual interface
Wants=sys-subsystem-net-devices-wlan0.device
After=sys-subsystem-net-devices-wlan0.device NetworkManager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=-/usr/sbin/iw dev wlan0 interface add wlan1 type __ap

[Install]
WantedBy=multi-user.target
"""

_AP_DISPATCHER_PATH = "/etc/NetworkManager/dispatcher.d/90-cocktailberry-ap"
# wlan1 up: Docker sets the iptables FORWARD policy to DROP, which cuts AP clients off from the
# internet despite NetworkManager's NAT, so re-apply accept rules on every AP interface up.
# wlan0 up/down: the uplink shares the single radio with the AP, so its (re)connects can take the
# AP down. Bring it back whenever it is meant to be on (autoconnect) but is not active.
_AP_DISPATCHER_SCRIPT = f"""#!/bin/sh
# Installed by CocktailBerry access point setup, removed on access point removal.
case "$1:$2" in
wlan1:up)
    iptables -C FORWARD -i wlan1 -j ACCEPT 2>/dev/null || iptables -I FORWARD -i wlan1 -j ACCEPT
    iptables -C FORWARD -o wlan1 -j ACCEPT 2>/dev/null || iptables -I FORWARD -o wlan1 -j ACCEPT
    ;;
wlan0:up | wlan0:down)
    [ "$(nmcli -g connection.autoconnect connection show {CONNECTION_NAME} 2>/dev/null)" = "yes" ] || exit 0
    case "$(nmcli -g GENERAL.STATE connection show {CONNECTION_NAME})" in activat*) exit 0 ;; esac
    nmcli --wait 0 connection up {CONNECTION_NAME}
    ;;
esac
"""


@dataclass
class ApStatus:
    configured: bool
    enabled: bool
    ssid: str
    password: str


def run_privileged(*args: str, check: bool = True, timeout: float = _TIMEOUT) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["sudo", "-n", *args], capture_output=True, text=True, timeout=timeout, check=False)
    if check and result.returncode != 0:
        # CalledProcessError's message omits stderr, which is where nmcli explains itself
        _logger.error(f"`{' '.join(args)}` failed: {result.stderr.strip()}")
        result.check_returncode()
    return result


def _write_root_file(path: str, content: str) -> None:
    subprocess.run(
        ["sudo", "-n", "tee", path], input=content, text=True, check=True, capture_output=True, timeout=_TIMEOUT
    )


def parse_nmcli_terse(output: str) -> dict[str, str]:
    """Parse `nmcli -t` key:value lines; nmcli backslash-escapes ':' and backslashes in values."""
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key] = value.replace("\\:", ":").replace("\\\\", "\\")
    return fields


def read_ap() -> ApStatus:
    """Read the AP profile from NetworkManager; anything failing means 'not configured'."""
    try:
        result = run_privileged(
            "nmcli", "-s", "-t", "-f", "802-11-wireless.ssid,802-11-wireless-security.psk,GENERAL.STATE",
            "connection", "show", CONNECTION_NAME, check=False,
        )  # fmt: skip
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        _logger.error(f"Could not query access point state: {e}")
        return ApStatus(False, False, DEFAULT_SSID, DEFAULT_PASSWORD)
    if result.returncode != 0:
        return ApStatus(False, False, DEFAULT_SSID, DEFAULT_PASSWORD)
    fields = parse_nmcli_terse(result.stdout)
    return ApStatus(
        configured=True,
        # GENERAL.* is only listed while the profile is active
        enabled=fields.get("GENERAL.STATE") == "activated",
        # an apply interrupted between `add` and `modify` leaves the psk unset; nmcli prints it as empty
        ssid=fields.get("802-11-wireless.ssid") or DEFAULT_SSID,
        password=fields.get("802-11-wireless-security.psk") or DEFAULT_PASSWORD,
    )


def apply_ap(enabled: bool, ssid: str, password: str) -> None:
    """Create or update the AP profile and bring it to the requested state.

    Raises CalledProcessError / TimeoutExpired when NetworkManager refuses.
    """
    current = read_ap()
    _install_system_files()
    if not current.configured:
        run_privileged(
            "nmcli", "connection", "add", "type", "wifi", "ifname", "wlan1", "con-name", CONNECTION_NAME, "ssid", ssid
        )  # fmt: skip
    run_privileged(
        "nmcli", "connection", "modify", CONNECTION_NAME,
        "802-11-wireless.ssid", ssid,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "ipv4.method", "shared",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", password,
        # WPA2-only without PMF: offering legacy WPA1 breaks some clients (RSNXE mismatch -> instant deauth)
        "wifi-sec.proto", "rsn",
        "wifi-sec.pmf", "disable",
        "connection.autoconnect", "yes" if enabled else "no",
        *_AUTOCONNECT_RETRIES,
    )  # fmt: skip
    if not enabled:
        run_privileged("nmcli", "connection", "down", CONNECTION_NAME, check=False)
        return
    unchanged = current.enabled and (current.ssid, current.password) == (ssid, password)
    if not unchanged:  # `con up` restarts an active AP, which kicks all clients, so only do it on real changes
        activate()


def refresh_installation() -> None:
    """Bring the system files and profile hardening of an existing AP up to date without touching its state."""
    if not read_ap().configured:
        return
    _install_system_files()
    run_privileged("nmcli", "connection", "modify", CONNECTION_NAME, *_AUTOCONNECT_RETRIES)


def _install_system_files() -> None:
    # idempotent; runs on every apply so existing installs pick up script changes.
    # installed before activation so the dispatcher fires on the first up event
    _write_root_file(_AP_DISPATCHER_PATH, _AP_DISPATCHER_SCRIPT)
    run_privileged("chmod", "755", _AP_DISPATCHER_PATH)
    _write_root_file(_AP_IFACE_UNIT_PATH, _AP_IFACE_UNIT)
    run_privileged("systemctl", "daemon-reload")
    run_privileged("systemctl", "enable", "--now", "cocktailberry-ap-iface.service")


def activate() -> None:
    # NetworkManager needs a moment to adopt the freshly created wlan1 before it can activate on it
    for attempt in range(5):
        if attempt:
            time.sleep(2)
        result = run_privileged("nmcli", "--wait", str(_UP_WAIT), "connection", "up", CONNECTION_NAME, check=False)
        if result.returncode == 0:
            return
    result.check_returncode()


def remove_ap() -> None:
    """Full teardown: profile, virtual interface, systemd unit and dispatcher script."""
    run_privileged("systemctl", "disable", "--now", "cocktailberry-ap-iface.service", check=False)
    run_privileged("iw", "dev", "wlan1", "del", check=False)
    run_privileged("nmcli", "connection", "delete", CONNECTION_NAME, check=False)
    run_privileged("rm", "-f", _AP_DISPATCHER_PATH, _AP_IFACE_UNIT_PATH, check=False)
    run_privileged("systemctl", "daemon-reload", check=False)


def wifi_qr_payload(ssid: str, password: str) -> str:
    """Wi-Fi QR string as read by phone cameras (WIFI:T:WPA;S:<ssid>;P:<password>;;)."""

    def escape(value: str) -> str:
        for char in r'\;,":':
            value = value.replace(char, f"\\{char}")
        return value

    return f"WIFI:T:WPA;S:{escape(ssid)};P:{escape(password)};;"


def ap_qr_png(ssid: str, password: str) -> bytes:
    buffer = io.BytesIO()
    qrcode.make(wifi_qr_payload(ssid, password)).save(buffer, format="PNG")
    return buffer.getvalue()
