import json

import typer
from InquirerPy import inquirer
from InquirerPy.base import Choice

from src.config.config_manager import CONFIG as cfg
from src.filepath import BLACKLIST_FILE
from src.logger_handler import LoggerHandler
from src.models import BlackList, OptionTiles

_logger = LoggerHandler("blacklist")


def generate_blacklist() -> None:
    file_data = json.loads(BLACKLIST_FILE.read_text()) if BLACKLIST_FILE.exists() else {}
    try:
        blacklist = BlackList(**file_data)
    except Exception:
        blacklist = BlackList(configs=[], options=OptionTiles())
    configs = inquirer.checkbox(
        message="Blacklisted configs:",
        choices=[Choice(value=k, enabled=k in blacklist.configs) for k in cfg.config_type],
    ).execute()
    options = inquirer.checkbox(
        message="Blacklisted options:",
        choices=[Choice(value=k, enabled=getattr(blacklist.options, k, False)) for k in OptionTiles.model_fields],
    ).execute()
    with BLACKLIST_FILE.open("w") as f:
        json.dump({"configs": configs, "options": options}, f, indent=2)
    typer.secho(f"Blacklist generated successfully at {BLACKLIST_FILE}!", fg=typer.colors.GREEN, bold=True)


class BlacklistManager:
    """Runtime singleton holding the producer-defined blacklist.

    The blacklist is read once from ``BLACKLIST_FILE``. Missing file is treated as
    "no blacklist" (the common end-user case). A malformed file is logged and
    falls back to an empty blacklist so a broken file never blocks startup.

    Enforcement is strictly UI-side: callers use ``is_config_blacklisted`` /
    ``is_tile_blacklisted`` to decide whether to show widgets in v1 (Qt) and v2
    (React). API endpoints remain reachable with the master password.
    """

    def __init__(self) -> None:
        self.blacklist: BlackList = self._empty()
        self.reload()

    @staticmethod
    def _empty() -> BlackList:
        return BlackList(configs=[], options=OptionTiles())

    def reload(self) -> None:
        if not BLACKLIST_FILE.exists():
            self.blacklist = self._empty()
            return
        try:
            file_data = json.loads(BLACKLIST_FILE.read_text())
            self.blacklist = BlackList(**file_data)
        except Exception as exc:
            _logger.log_event(
                "WARNING",
                f"Could not parse blacklist file at {BLACKLIST_FILE}, ignoring it: {exc}",
            )
            self.blacklist = self._empty()

    def is_config_blacklisted(self, config_name: str) -> bool:
        return config_name in self.blacklist.configs

    def is_tile_blacklisted(self, tile_name: str) -> bool:
        return bool(getattr(self.blacklist.options, tile_name, False))

    def blacklisted_tiles(self) -> list[str]:
        """List of option-tile names currently blacklisted (for API responses)."""
        return [name for name in OptionTiles.model_fields if self.is_tile_blacklisted(name)]


BLACKLIST = BlacklistManager()
