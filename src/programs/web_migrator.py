from pathlib import Path

import typer

new_backend_script_content = """
source ~/.env-cocktailberry/bin/activate
python runme.py api
"""

old_backend_script_content = """
source ~/.env-cocktailberry/bin/activate
export QT_SCALE_FACTOR=1
cd ~/CocktailBerry/
python runme.py
"""

new_web_entry = """
[Desktop Entry]
Type=Application
Name=CocktailBerry Web
Exec=chromium-browser --kiosk http://localhost:5173
Terminal=false
"""
script_entry_path = Path.home() / "launcher.sh"
web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def replace_backend_entry():
    """Replace the content for the shell script to start the backend."""
    if script_entry_path.exists():
        backup_path = script_entry_path.with_suffix(".bak")
        script_entry_path.rename(backup_path)
        script_entry_path.write_text(new_backend_script_content)
    else:
        typer.echo(f"Script {script_entry_path} not found. Creating a new one.")
        script_entry_path.write_text(new_backend_script_content)


def create_web_entry():
    """Create the web entry for the autostart."""
    web_entry_path.write_text(new_web_entry)


def _remove_web_entry():
    """Remove the web entry for the autostart."""
    if web_entry_path.exists():
        web_entry_path.unlink()
        typer.echo("Removed web entry.")
    else:
        typer.echo("Web entry not found. Nothing to remove.")


def roll_back_to_qt_setup():
    """Roll back to the Qt setup."""
    _remove_web_entry()
    # use the backup file if it exists
    script_entry_path.write_text(old_backend_script_content)
