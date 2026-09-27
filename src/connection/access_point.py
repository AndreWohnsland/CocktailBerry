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
# Docker sets the iptables FORWARD policy to DROP, which cuts AP clients off from the internet
# despite NetworkManager's NAT. Re-apply accept rules on every AP interface up (boot, reactivation).
_AP_DISPATCHER_SCRIPT = """#!/bin/sh
# Installed by CocktailBerry access point setup, removed on access point removal.
[ "$1" = "wlan1" ] && [ "$2" = "up" ] || exit 0
iptables -C FORWARD -i wlan1 -j ACCEPT 2>/dev/null || iptables -I FORWARD -i wlan1 -j ACCEPT
iptables -C FORWARD -o wlan1 -j ACCEPT 2>/dev/null || iptables -I FORWARD -o wlan1 -j ACCEPT
"""


@dataclass
class ApStatus:
    configured: bool
    enabled: bool
    ssid: str
    password: str


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["sudo", *args], capture_output=True, text=True, timeout=_TIMEOUT, check=False)
    if check and result.returncode != 0:
        # CalledProcessError's message omits stderr, which is where nmcli explains itself
        _logger.error(f"`{' '.join(args)}` failed: {result.stderr.strip()}")
        result.check_returncode()
    return result


def _write_root_file(path: str, content: str) -> None:
    subprocess.run(["sudo", "tee", path], input=content, text=True, check=True, capture_output=True, timeout=_TIMEOUT)


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
        result = _run(
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
    if not current.configured:
        _install_system_files()
        _run("nmcli", "connection", "add", "type", "wifi", "ifname", "wlan1", "con-name", CONNECTION_NAME, "ssid", ssid)
    _run(
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
    )  # fmt: skip
    if not enabled:
        _run("nmcli", "connection", "down", CONNECTION_NAME, check=False)
        return
    unchanged = current.enabled and (current.ssid, current.password) == (ssid, password)
    if not unchanged:  # `con up` restarts an active AP, which kicks all clients, so only do it on real changes
        _activate()


def _install_system_files() -> None:
    # install before activation so the dispatcher fires on the first up event
    _write_root_file(_AP_DISPATCHER_PATH, _AP_DISPATCHER_SCRIPT)
    _run("chmod", "755", _AP_DISPATCHER_PATH)
    _write_root_file(_AP_IFACE_UNIT_PATH, _AP_IFACE_UNIT)
    _run("systemctl", "daemon-reload")
    _run("systemctl", "enable", "--now", "cocktailberry-ap-iface.service")


def _activate() -> None:
    # NetworkManager needs a moment to adopt the freshly created wlan1 before it can activate on it
    for attempt in range(5):
        if attempt:
            time.sleep(2)
        result = _run("nmcli", "connection", "up", CONNECTION_NAME, check=False)
        if result.returncode == 0:
            return
    result.check_returncode()


def remove_ap() -> None:
    """Full teardown: profile, virtual interface, systemd unit and dispatcher script."""
    _run("systemctl", "disable", "--now", "cocktailberry-ap-iface.service", check=False)
    _run("iw", "dev", "wlan1", "del", check=False)
    _run("nmcli", "connection", "delete", CONNECTION_NAME, check=False)
    _run("rm", "-f", _AP_DISPATCHER_PATH, _AP_IFACE_UNIT_PATH, check=False)
    _run("systemctl", "daemon-reload", check=False)


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
