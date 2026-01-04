from pathlib import Path

ROOT_PATH = Path(__file__).parents[2].absolute()
COCKTAIL_WEB_DESKTOP = ROOT_PATH / "scripts" / "cocktail_web.desktop"

script_entry_path = Path.home() / "launcher.sh"
web_launcher_path = Path.home() / "CocktailBerry" / "scripts" / "v2-launcher.sh"
desktop_file = Path.home() / "Desktop" / "cocktail_web.desktop"
web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def replace_backend_script() -> None:
    """Replace the content for the shell script to start the backend."""
    backup_path = script_entry_path.with_suffix(".bak")
    if script_entry_path.exists() and not script_entry_path.is_symlink() and not backup_path.exists():
        script_entry_path.rename(backup_path)
    if script_entry_path.exists() or script_entry_path.is_symlink():
        script_entry_path.unlink()
    script_entry_path.symlink_to(web_launcher_path)
    web_launcher_path.chmod(0o755)


def add_web_desktop_file() -> None:
    desktop_file.write_text(COCKTAIL_WEB_DESKTOP.read_text())
    desktop_file.chmod(0o755)


def _create_web_entry() -> None:
    """Create the web entry for the autostart."""
    web_entry_path.write_text(COCKTAIL_WEB_DESKTOP.read_text())


# This section need to be run as root in a subprocess
if __name__ == "__main__":
    _create_web_entry()
    print("Switched to web setup successfully.")
