from pathlib import Path

script_entry_path = Path.home() / "launcher.sh"
qt_launcher_path = Path.home() / "CocktailBerry" / "scripts" / "v1-launcher.sh"
web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def _remove_web_entry() -> None:
    """Remove the web entry for the autostart."""
    if web_entry_path.exists():
        web_entry_path.unlink()
        print("Removed web entry.")
    else:
        print("Web entry not found. Nothing to remove.")


def roll_back_to_qt_script() -> None:
    """Roll back to the Qt setup."""
    if script_entry_path.exists() or script_entry_path.is_symlink():
        script_entry_path.unlink()
    script_entry_path.symlink_to(qt_launcher_path)
    qt_launcher_path.chmod(0o755)


# This section need to be run as root in a subprocess
if __name__ == "__main__":
    _remove_web_entry()
    print("Switched to Qt setup successfully.")
