from pathlib import Path

web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def _remove_web_entry() -> None:
    """Remove the web entry for the autostart."""
    if web_entry_path.exists():
        web_entry_path.unlink()
        print("Removed web entry.")
    else:
        print("Web entry not found. Nothing to remove.")


def roll_back_to_qt_script() -> None:
    """Point the launcher at the v1 (Qt) backend, preserving any user customization."""
    # Runtime import: keeps this module runnable as a standalone root script (__main__),
    # where the repo root is not on sys.path and top-level `src.*` imports would fail.
    from src.migration.launcher import switch_launcher

    switch_launcher("v1")


# This section need to be run as root in a subprocess
if __name__ == "__main__":
    _remove_web_entry()
    print("Switched to Qt setup successfully.")
