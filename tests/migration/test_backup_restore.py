from pathlib import Path

from src.filepath import CUSTOM_CONFIG_FILE, DATABASE_PATH, VERSION_FILE
from src.migration.backup import files_for_groups, restore_backup


def test_restores_only_the_selected_groups_plus_version(tmp_path: Path) -> None:
    backup = tmp_path / "backup"
    backup.mkdir()
    for name in (VERSION_FILE.name, CUSTOM_CONFIG_FILE.name, DATABASE_PATH.name):
        (backup / name).write_text(name)
    # redirect the real targets into tmp, the selection logic only cares about the file names
    install = tmp_path / "install"
    install.mkdir()
    targets = [install / f.name for f in files_for_groups(["config"])]

    restore_backup(backup, targets)

    assert {f.name for f in install.iterdir()} == {VERSION_FILE.name, CUSTOM_CONFIG_FILE.name}
