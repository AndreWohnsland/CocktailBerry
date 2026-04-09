import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import typer

from src import __version__
from src.filepath import (
    ADDON_FOLDER,
    ADDON_SKELETON,
    DISPENSER_ADDON_FOLDER,
    DISPENSER_EXTENSION_SKELETON,
    HARDWARE_ADDON_FOLDER,
    HARDWARE_EXTENSION_SKELETON,
)


@dataclass
class _SkeletonConfig:
    folder: Path
    skeleton: Path
    label: str
    name_placeholder: str


SKELETON_OPTIONS = Literal["addon", "dispenser", "hardware"]

_SKELETON_CONFIGS: dict[SKELETON_OPTIONS, _SkeletonConfig] = {
    "addon": _SkeletonConfig(
        ADDON_FOLDER,
        ADDON_SKELETON,
        "addon",
        "ADDON_NAME_HOLDER",
    ),
    "dispenser": _SkeletonConfig(
        DISPENSER_ADDON_FOLDER,
        DISPENSER_EXTENSION_SKELETON,
        "dispenser extension",
        "EXTENSION_NAME_HOLDER",
    ),
    "hardware": _SkeletonConfig(
        HARDWARE_ADDON_FOLDER,
        HARDWARE_EXTENSION_SKELETON,
        "hardware extension",
        "EXTENSION_NAME_HOLDER",
    ),
}


def generate_skeleton_for(skeleton: SKELETON_OPTIONS, name: str) -> None:
    """Generate a skeleton file for the given extension type and name."""
    config = _SKELETON_CONFIGS[skeleton]
    file_name = re.sub(r"\W", "", name.replace(" ", "_").lower())
    extension_path = config.folder / f"{file_name}.py"
    if extension_path.exists():
        msg = f"There is already a {config.label} created under the {name=} in {file_name}.py"
        typer.echo(typer.style(f"{msg}, aborting...", fg=typer.colors.RED, bold=True))
        raise typer.Exit()
    config.folder.mkdir(parents=True, exist_ok=True)
    extension_path.write_text(
        config.skeleton.read_text(encoding="utf-8")
        .replace(config.name_placeholder, name)
        .replace("VERSION_HOLDER", __version__),
        encoding="utf-8",
    )
    typer.echo(
        typer.style(
            f"{config.label.capitalize()} file was created at {extension_path}", fg=typer.colors.GREEN, bold=True
        )
    )
