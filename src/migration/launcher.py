from pathlib import Path
from typing import Literal

from src.filepath import SCRIPTS_FOLDER

Version = Literal["v1", "v2"]


def switch_launcher(target: Version) -> None:
    """Point ~/launcher.sh at the given version's launcher, preserving user edits.

    The installer sets ~/launcher.sh as a symlink to the tracked ``v1-launcher.sh`` /
    ``v2-launcher.sh``. A launcher that is a real file (not that symlink) is treated as a user
    customization: it is backed up under the version it belongs to before switching, and
    restored (then the backup removed) when switching back to that version. Version-suffixed
    backups (``launcher.v1.bak`` / ``launcher.v2.bak``) keep a customized v1 and a customized
    v2 launcher from overwriting each other.
    """
    home = Path.home()
    source: Version = "v1" if target == "v2" else "v2"
    launcher = home / "launcher.sh"
    target_script = SCRIPTS_FOLDER / f"{target}-launcher.sh"
    target_backup = home / f"launcher.{target}.bak"

    # Current launcher belongs to the source version: keep user edits, drop the stock symlink.
    if launcher.is_symlink():
        launcher.unlink()
    elif launcher.exists():
        launcher.rename(home / f"launcher.{source}.bak")

    # Restore a previous customization for the target version, else use the stock script.
    if target_backup.exists():
        target_backup.rename(launcher)
    else:
        launcher.symlink_to(target_script)
    target_script.chmod(0o755)
