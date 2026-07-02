from pathlib import Path

import pytest

from src.migration import launcher
from src.migration.launcher import switch_launcher


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "v1-launcher.sh").write_text("stock v1\n")
    (scripts / "v2-launcher.sh").write_text("stock v2\n")
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    monkeypatch.setattr(launcher, "SCRIPTS_FOLDER", scripts)
    return home_dir


def test_fresh_switch_creates_symlink(home: Path) -> None:
    launcher_file = home / "launcher.sh"

    switch_launcher("v2")

    assert launcher_file.is_symlink()
    assert launcher_file.resolve().name == "v2-launcher.sh"
    assert not (home / "launcher.v1.bak").exists()


def test_custom_launcher_is_backed_up_and_restored(home: Path) -> None:
    launcher_file = home / "launcher.sh"

    # user starts on a customized v1 launcher (real file, not a symlink)
    launcher_file.write_text("my custom v1\n")

    switch_launcher("v2")
    assert launcher_file.is_symlink()
    assert (home / "launcher.v1.bak").read_text() == "my custom v1\n"

    # switching back restores the customization and removes the backup
    switch_launcher("v1")
    assert not launcher_file.is_symlink()
    assert launcher_file.read_text() == "my custom v1\n"
    assert not (home / "launcher.v1.bak").exists()


def test_both_versions_custom_do_not_clobber(home: Path) -> None:
    launcher_file = home / "launcher.sh"

    launcher_file.write_text("custom v1\n")  # v1 customized
    switch_launcher("v2")
    launcher_file.unlink()
    launcher_file.write_text("custom v2\n")  # now customize v2 too

    switch_launcher("v1")  # backs up v2, restores v1
    assert launcher_file.read_text() == "custom v1\n"
    assert (home / "launcher.v2.bak").read_text() == "custom v2\n"

    switch_launcher("v2")  # backs up v1, restores v2
    assert launcher_file.read_text() == "custom v2\n"
    assert (home / "launcher.v1.bak").read_text() == "custom v1\n"
