from pathlib import Path

from filepath import COCKTAIL_WEB_DESKTOP

new_backend_script_content = """source ~/.env-cocktailberry/bin/activate
cd ~/CocktailBerry/
python runme.py api
"""

script_entry_path = Path.home() / "launcher.sh"
desktop_file = Path.home() / "Desktop" / "cocktail_web.desktop"
web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def replace_backend_script():
    """Replace the content for the shell script to start the backend."""
    backup_path = script_entry_path.with_suffix(".bak")
    if script_entry_path.exists() and not backup_path.exists():
        script_entry_path.rename(backup_path)
    script_entry_path.write_text(new_backend_script_content)
    script_entry_path.chmod(0o755)


def add_web_desktop_file():
    desktop_file.write_text(COCKTAIL_WEB_DESKTOP.read_text())
    desktop_file.chmod(0o755)


def _create_web_entry():
    """Create the web entry for the autostart."""
    web_entry_path.write_text(COCKTAIL_WEB_DESKTOP.read_text())


# This section need to be run as root in a subprocess
if __name__ == "__main__":
    _create_web_entry()
    print("Switched to web setup successfully.")
