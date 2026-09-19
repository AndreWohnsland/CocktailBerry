from pathlib import Path

from src.api.routers.options import _find_backup_root
from src.filepath import VERSION_FILE


def _write_backup(folder: Path) -> Path:
    """Create a minimal backup folder, the version file is what marks it as one."""
    folder.mkdir(parents=True)
    (folder / VERSION_FILE.name).write_text("[DEFAULT]\nlocalversion = 3.3.0\n")
    (folder / "Cocktail_database.db").write_text("db")
    return folder


def test_finds_the_folder_created_by_the_backup_export(tmp_path: Path) -> None:
    backup = _write_backup(tmp_path / "CocktailBerry_backup_2026-09-19")
    assert _find_backup_root(tmp_path) == backup


def test_ignores_macos_resource_fork_sibling(tmp_path: Path) -> None:
    """Repacking a backup on macOS adds __MACOSX next to the backup folder."""
    backup = _write_backup(tmp_path / "CocktailBerry_backup_2026-09-19")
    (tmp_path / "__MACOSX").mkdir()
    assert _find_backup_root(tmp_path) == backup


def test_finds_backup_zipped_without_a_wrapping_folder(tmp_path: Path) -> None:
    """Zipping the contents instead of the folder leaves the files at the top level."""
    (tmp_path / VERSION_FILE.name).write_text("[DEFAULT]\nlocalversion = 3.3.0\n")
    assert _find_backup_root(tmp_path) == tmp_path


def test_returns_none_when_no_version_file_present(tmp_path: Path) -> None:
    (tmp_path / "holiday_photos").mkdir()
    assert _find_backup_root(tmp_path) is None
