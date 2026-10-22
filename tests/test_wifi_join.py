"""The join must never leave the machine without its access point, NetworkManager stays faked."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field

import pytest

from src.connection import access_point, wifi
from src.connection.access_point import CONNECTION_NAME

AP_FIELDS = "802-11-wireless.ssid:CocktailBerry\n802-11-wireless-security.psk:cocktailconnect\n"
JOIN_ERROR = "Error: Connection activation failed: (7) Secrets were required, but not provided."


@dataclass
class FakeNetworkManager:
    """Just enough nmcli to drive `wifi.join`; commands arrive without the leading sudo."""

    ap_configured: bool = True
    ap_active: bool = True
    join_rc: int = 0
    ap_up_rc: int = 0
    ap_up_hangs: bool = False  # NetworkManager never answers, the subprocess call times out
    connect_kills_ap: bool = False  # the uplink moved the shared radio to another channel
    uplink: str | None = "OldNet"
    psk: dict[str, str] = field(default_factory=lambda: {"OldNet": "oldsecret"})
    profiles: set[str] = field(default_factory=lambda: {"uuid-ap", "uuid-OldNet"})
    commands: list[list[str]] = field(default_factory=list)

    def run(self, command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        args = command[2:]  # strip `sudo -n`
        self.commands.append(args)
        rc, out, err = 0, "", ""
        if args[-3:] == ["connection", "show", CONNECTION_NAME]:
            if not self.ap_configured:
                rc = 10
            else:
                out = AP_FIELDS + ("GENERAL.STATE:activated\n" if self.ap_active else "")
        elif args[-3:-1] == ["connection", "show"] and "-g" in args:
            out = self.psk.get(args[-1], "") if "psk" in args[args.index("-g") + 1] else args[-1]
        elif "UUID" in args and "show" in args:
            out = "\n".join(self.profiles)
        elif args[-3:] == ["dev", "show", wifi.STA_IFACE]:
            out = f"GENERAL.CONNECTION:{self.uplink or ''}\nIP4.ADDRESS[1]:192.168.1.5/24\n"
        else:
            rc, err = self._change(command, args)
        return subprocess.CompletedProcess(command, rc, out, err)

    def _change(self, command: list[str], args: list[str]) -> tuple[int, str]:
        if "connect" in args:
            ssid = args[args.index("connect") + 1]
            self.profiles.add(f"uuid-{ssid}")  # nmcli keeps the profile even when activation fails
            if self.join_rc:
                return self.join_rc, JOIN_ERROR + "\n"
            self.uplink = ssid
            self.ap_active = self.ap_active and not self.connect_kills_ap
        elif args[1:3] == ["connection", "delete"]:
            self.profiles.discard(args[3])
        elif args[1:3] == ["connection", "modify"] and "wifi-sec.psk" in args:
            self.psk[args[3]] = args[-1]
        elif args[-2:] == ["up", CONNECTION_NAME]:
            if self.ap_up_hangs:
                raise subprocess.TimeoutExpired(command, 30)
            self.ap_active = self.ap_up_rc == 0
            return self.ap_up_rc, "Error: Connection activation failed: channel busy\n" if self.ap_up_rc else ""
        return 0, ""

    def calls(self, *prefix: str) -> list[list[str]]:
        return [c for c in self.commands if c[: len(prefix)] == list(prefix)]

    def restored_old_uplink(self) -> bool:
        return bool(self.calls("nmcli", "--wait", "25", "connection", "up", "OldNet"))


@pytest.fixture
def nm(monkeypatch: pytest.MonkeyPatch) -> FakeNetworkManager:
    fake = FakeNetworkManager()
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(time, "sleep", lambda _: None)
    return fake


def test_failed_join_is_rolled_back_with_reason(nm: FakeNetworkManager) -> None:
    nm.join_rc = 4
    result = wifi.join("NewNet", "secret")

    assert not result.success
    assert result.reason == JOIN_ERROR
    assert "uuid-NewNet" not in nm.profiles, "stale profile would make NetworkManager retry on its own"
    assert nm.restored_old_uplink()
    assert nm.ap_active


def test_retyping_the_current_uplink_wrongly_keeps_its_password(nm: FakeNetworkManager) -> None:
    nm.join_rc = 4
    wifi.join("OldNet", "typo")  # nmcli reuses the existing profile and overwrites its psk

    assert nm.psk["OldNet"] == "oldsecret"


def test_successful_join_keeps_an_active_access_point_untouched(nm: FakeNetworkManager) -> None:
    result = wifi.join("NewNet", "secret")

    assert result.success
    assert nm.uplink == "NewNet"
    assert not nm.calls("nmcli", "--wait", "25", "connection", "up", CONNECTION_NAME), "re-up kicks every client"
    assert not nm.calls("nmcli", "connection", "delete")


def test_join_that_drops_the_access_point_restores_it(nm: FakeNetworkManager) -> None:
    nm.connect_kills_ap = True
    result = wifi.join("NewNet", "secret")

    assert result.success
    assert nm.ap_active


def test_join_is_rolled_back_when_access_point_cannot_come_back(nm: FakeNetworkManager) -> None:
    nm.connect_kills_ap = True
    nm.ap_up_rc = 4
    result = wifi.join("NewNet", "secret")

    assert not result.success
    assert result.reason == "Error: Connection activation failed: channel busy"
    assert "uuid-NewNet" not in nm.profiles
    assert nm.restored_old_uplink()


def test_hanging_access_point_restore_still_rolls_back(nm: FakeNetworkManager) -> None:
    nm.connect_kills_ap = True
    nm.ap_up_hangs = True
    result = wifi.join("NewNet", "secret")

    assert not result.success
    assert "uuid-NewNet" not in nm.profiles
    assert nm.restored_old_uplink()


def test_without_access_point_a_failed_join_only_restores_the_uplink(nm: FakeNetworkManager) -> None:
    nm.ap_configured = False
    nm.ap_active = False
    nm.join_rc = 4
    result = wifi.join("NewNet", "secret")

    assert not result.success
    assert not nm.calls("nmcli", "--wait", "25", "connection", "up", CONNECTION_NAME)
    assert nm.restored_old_uplink()


def test_refresh_installation_never_restarts_an_active_access_point(nm: FakeNetworkManager) -> None:
    access_point.refresh_installation()

    assert not nm.calls("nmcli", "--wait", "25", "connection", "up")
    assert not nm.calls("nmcli", "connection", "down")
    assert nm.calls("nmcli", "connection", "modify", CONNECTION_NAME, "connection.autoconnect-retries", "0")


def test_refresh_installation_is_a_noop_without_access_point(nm: FakeNetworkManager) -> None:
    nm.ap_configured = False
    access_point.refresh_installation()

    assert not nm.calls("tee")
    assert not nm.calls("nmcli", "connection", "modify")
