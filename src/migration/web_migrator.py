from pathlib import Path

new_backend_script_content = """
source ~/.env-cocktailberry/bin/activate
cd ~/CocktailBerry/
python runme.py api
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


def replace_backend_script():
    """Replace the content for the shell script to start the backend."""
    if script_entry_path.exists():
        backup_path = script_entry_path.with_suffix(".bak")
        script_entry_path.rename(backup_path)
        script_entry_path.write_text(new_backend_script_content)
    else:
        print(f"Script {script_entry_path} not found. Creating a new one.")
        script_entry_path.write_text(new_backend_script_content)
    script_entry_path.chmod(0o755)


def _create_web_entry():
    """Create the web entry for the autostart."""
    web_entry_path.write_text(new_web_entry)


# This section need to be run as root in a subprocess
if __name__ == "__main__":
    _create_web_entry()
    print("Switched to web setup successfully.")
