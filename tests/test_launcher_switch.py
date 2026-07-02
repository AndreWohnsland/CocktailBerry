from pathlib import Path

import pytest

from src.migration import launcher
from src.migration.launcher import switch_launcher

V1_CONTENT = "uv run --extra v1 --extra nfc runme.py\n"
V2_CONTENT = "uv run --extra nfc api.py\n"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "v1-launcher.sh").write_text(V1_CONTENT)
    (scripts / "v2-launcher.sh").write_text(V2_CONTENT)
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
    launcher_file.write_text("# my edit\n" + V1_CONTENT)

    switch_launcher("v2")
    assert launcher_file.is_symlink()
    # labelled by content, not by the assumed "other" version
    assert (home / "launcher.v1.bak").read_text() == "# my edit\n" + V1_CONTENT

    # switching back restores the customization and removes the backup
    switch_launcher("v1")
    assert not launcher_file.is_symlink()
    assert launcher_file.read_text() == "# my edit\n" + V1_CONTENT
    assert not (home / "launcher.v1.bak").exists()


def test_both_versions_custom_do_not_clobber(home: Path) -> None:
    launcher_file = home / "launcher.sh"

    launcher_file.write_text("# v1 edit\n" + V1_CONTENT)  # v1 customized
    switch_launcher("v2")
    launcher_file.unlink()
    launcher_file.write_text("# v2 edit\n" + V2_CONTENT)  # now customize v2 too

    switch_launcher("v1")  # backs up v2 (by content), restores v1
    assert launcher_file.read_text() == "# v1 edit\n" + V1_CONTENT
    assert (home / "launcher.v2.bak").read_text() == "# v2 edit\n" + V2_CONTENT

    switch_launcher("v2")  # backs up v1 (by content), restores v2
    assert launcher_file.read_text() == "# v2 edit\n" + V2_CONTENT
    assert (home / "launcher.v1.bak").read_text() == "# v1 edit\n" + V1_CONTENT


def test_preserve_false_discards_and_creates_stock_symlink(home: Path) -> None:
    launcher_file = home / "launcher.sh"

    # an old customized launcher the migration wants to normalise away
    launcher_file.write_text("# ancient\n" + V1_CONTENT)

    switch_launcher("v1", preserve=False)

    assert launcher_file.is_symlink()
    assert launcher_file.resolve().name == "v1-launcher.sh"
    # nothing backed up, nothing restored
    assert not (home / "launcher.v1.bak").exists()
    assert not (home / "launcher.v2.bak").exists()
