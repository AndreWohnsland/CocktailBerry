import json

import typer
from InquirerPy import inquirer
from InquirerPy.base import Choice

from src.config.config_manager import CONFIG as cfg
from src.filepath import BLACKLIST_FILE
from src.models import BlackList, OptionTiles


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
        choices=[
            Choice(value=k, enabled=getattr(blacklist.options, k, False)) for k in list(OptionTiles.model_fields.keys())
        ],
    ).execute()
    with BLACKLIST_FILE.open("w") as f:
        json.dump({"configs": configs, "options": options}, f, indent=2)
    typer.secho(f"Blacklist generated successfully at {BLACKLIST_FILE}!", fg=typer.colors.GREEN, bold=True)
