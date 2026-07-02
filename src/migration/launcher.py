from pathlib import Path
from typing import Literal

from src.filepath import SCRIPTS_FOLDER

Version = Literal["v1", "v2"]


def launcher_path() -> Path:
    """Return the path of the launcher script the installer manages (~/launcher.sh)."""
    return Path.home() / "launcher.sh"


def _detect_version(launcher: Path) -> Version:
    """Detect which version a launcher script belongs to from its content.

    A v1 launcher runs ``runme.py``, a v2 launcher runs ``api.py``.
    """
    return "v1" if "runme.py" in launcher.read_text() else "v2"


def switch_launcher(target: Version, preserve: bool = True) -> None:
    """Point ~/launcher.sh at the given version's launcher.

    The installer sets ~/launcher.sh as a symlink to the tracked ``v1-launcher.sh`` /
    ``v2-launcher.sh``. A launcher that is a real file (not that symlink) is a user
    customization.

    With ``preserve`` (the default, used by the user-facing switch commands) such a
    customization is backed up under the version it actually is (detected from its content) and
    restored (then the backup removed) when switching back to that version. Version-suffixed
    backups (``launcher.v1.bak`` / ``launcher.v2.bak``) keep a customized v1 and a customized v2
    launcher from overwriting each other.

    With ``preserve=False`` (used by the one-time migration that normalises an old launcher to
    the current form) the current launcher is discarded and the stock symlink is always created.
    """
    home = Path.home()
    launcher = launcher_path()
    target_script = SCRIPTS_FOLDER / f"{target}-launcher.sh"
    target_backup = home / f"launcher.{target}.bak"

    if launcher.is_symlink():
        launcher.unlink()
    elif launcher.exists():
        if preserve:
            launcher.rename(home / f"launcher.{_detect_version(launcher)}.bak")
        else:
            launcher.unlink()

    if preserve and target_backup.exists():
        target_backup.rename(launcher)
    else:
        launcher.symlink_to(target_script)
    target_script.chmod(0o755)
