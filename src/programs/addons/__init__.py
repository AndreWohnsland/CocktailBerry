import contextlib
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

import typer

from src import __version__
from src.config.config_types import ConfigClass
from src.filepath import (
    ADDON_FOLDER,
    ADDON_SKELETON,
    CARRIAGE_ADDON_FOLDER,
    CARRIAGE_EXTENSION_SKELETON,
    DISPENSER_ADDON_FOLDER,
    DISPENSER_EXTENSION_SKELETON,
    HARDWARE_ADDON_FOLDER,
    HARDWARE_EXTENSION_SKELETON,
    SCALE_ADDON_FOLDER,
    SCALE_EXTENSION_SKELETON,
)
from src.models import Cocktail

with contextlib.suppress(ModuleNotFoundError):
    from PyQt6.QtWidgets import QVBoxLayout


@runtime_checkable
class AddonInterface(Protocol):
    def version(self) -> str:
        """Return the version of the addon."""
        return getattr(self, "ADDON_VERSION", "1.0.0")

    def define_configuration(self) -> None:
        """Define configuration for the addon."""

    def setup(self) -> None:
        """Init the addon."""

    def cleanup(self) -> None:
        """Clean up the addon."""

    def before_cocktail(self, data: dict[str, Any]) -> None:
        """Logic to be executed before the cocktail."""

    def after_cocktail(self, data: dict[str, Any]) -> None:
        """Logic to be executed after the cocktail."""

    def build_gui(
        self,
        container: "QVBoxLayout",
        button_generator: Callable[[str, Callable[[], None]], None],
    ) -> bool:
        """Logic to build up the addon GUI."""
        return False

    def cocktail_trigger(self, prepare: Callable[[Cocktail], tuple[bool, str]]) -> None:
        """Will be executed in the background loop and can trigger a cocktail preparation.

        Use the prepare function to start a cocktail preparation with prepare(cocktail).
        Return if cocktail preparation was successful and a message.
        """


class BaseHardwareExtension[ConfigT: ConfigClass](ABC):
    """Base class for custom hardware extensions."""

    @abstractmethod
    def create(self, config: ConfigT) -> Any:
        """Create and return the shared hardware instance."""

    @abstractmethod
    def cleanup(self, instance: Any) -> None:
        """Release resources for a previously created hardware instance."""


@dataclass
class _SkeletonConfig:
    folder: Path
    skeleton: Path
    label: str
    name_placeholder: str


SKELETON_OPTIONS = Literal["addon", "dispenser", "hardware", "scale", "carriage"]

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
    "scale": _SkeletonConfig(
        SCALE_ADDON_FOLDER,
        SCALE_EXTENSION_SKELETON,
        "scale extension",
        "EXTENSION_NAME_HOLDER",
    ),
    "carriage": _SkeletonConfig(
        CARRIAGE_ADDON_FOLDER,
        CARRIAGE_EXTENSION_SKELETON,
        "carriage extension",
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
