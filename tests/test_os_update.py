"""``update_os`` reports whether it succeeded, because that now gates a reboot.

Both UIs reboot into the updated system only when this returns True. Getting the
result wrong either takes a working machine down for nothing or leaves it running
a half-applied update.
"""

from __future__ import annotations

import subprocess

import pytest

from src import utils


@pytest.fixture(autouse=True)
def _debian(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utils.distro, "id", lambda: "raspbian")
    # the real one writes an OS_UPDATE event into the live database
    monkeypatch.setattr("src.database_commander.DatabaseCommander.save_event", lambda *a, **kw: None)


def test_successful_update_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utils.subprocess, "run", lambda *a, **kw: None)
    assert utils.update_os() is True


def test_failed_update_reports_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, "apt-get")

    monkeypatch.setattr(utils.subprocess, "run", fail)
    assert utils.update_os() is False


def test_unsupported_distribution_reports_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utils.distro, "id", lambda: "plan9")

    def explode(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("must not run a package manager on an unknown distribution")

    monkeypatch.setattr(utils.subprocess, "run", explode)
    assert utils.update_os() is False
