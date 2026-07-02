from pathlib import Path

ROOT_PATH = Path(__file__).parents[2].absolute()
COCKTAIL_WEB_DESKTOP = ROOT_PATH / "scripts" / "cocktail_web.desktop"

desktop_file = Path.home() / "Desktop" / "cocktail_web.desktop"
web_entry_path = Path("/etc/xdg/autostart/cocktail_web.desktop")


def replace_backend_script() -> None:
    """Point the launcher at the v2 backend, preserving any user customization."""
    # Runtime import: keeps this module runnable as a standalone root script (__main__),
    # where the repo root is not on sys.path and top-level `src.*` imports would fail.
    from src.migration.launcher import switch_launcher

    switch_launcher("v2")


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
