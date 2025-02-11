from pathlib import Path

old_backend_script_content = """export QT_SCALE_FACTOR=1
create_or_update_venv() {
  system_python_version=$(python -V | awk '{print $2}')
  if [ -f ".venv/bin/python" ]; then
    venv_python_version=$(.venv/bin/python -V | awk '{print $2}')
  else
    venv_python_version=""
  fi

  if [ "$venv_python_version" != "$system_python_version" ]; then
    uv venv --system-site-packages --python "$system_python_version"
    echo "Virtual environment created/updated."
  else
    echo "Virtual environment is up-to-date."
  fi
}

cd ~/CocktailBerry/ || echo "Did not find ~/CocktailBerry/"
create_or_update_venv
uv run --python "$(python -V | awk '{print $2}')" --all-extras runme.py
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


def roll_back_to_qt_script():
    """Roll back to the Qt setup."""
    # use the backup file if it exists
    script_entry_path.write_text(old_backend_script_content)


# This section need to be run as root in a subprocess
if __name__ == "__main__":
    _remove_web_entry()
    print("Switched to Qt setup successfully.")
