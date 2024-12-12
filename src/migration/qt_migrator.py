from pathlib import Path

old_backend_script_content = """
source ~/.env-cocktailberry/bin/activate
export QT_SCALE_FACTOR=1
cd ~/CocktailBerry/
python runme.py
"""

script_entry_path = Path.home() / "launcher.sh"
web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def _remove_web_entry():
    """Remove the web entry for the autostart."""
    if web_entry_path.exists():
        web_entry_path.unlink()
        print("Removed web entry.")
    else:
        print("Web entry not found. Nothing to remove.")


def roll_back_to_qt_setup():
    """Roll back to the Qt setup."""
    _remove_web_entry()
    # use the backup file if it exists
    script_entry_path.write_text(old_backend_script_content)


if __name__ == "__main__":
    roll_back_to_qt_setup()
    print("Switched to Qt setup successfully.")
