from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

import typer

from src import __version__
from src.config.config_manager import CONFIG as cfg
from src.config.config_types import BasePumpConfig, ChooseOptions, ConfigInterface, DictType, FloatType, IntType
from src.config.validators import build_number_limiter
from src.filepath import DISPENSER_ADDON_FOLDER, DISPENSER_EXTENSION_SKELETON
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser

_logger = LoggerHandler("DispenserExtensionManager")
_check_extension = "please check dispenser extension or contact provider"

# Shared BasePumpConfig fields auto-injected into every dispenser extension.
_SHARED_PUMP_FIELDS: dict[str, ConfigInterface[Any]] = {
    "pump_type": ChooseOptions.dispenser,
    "volume_flow": FloatType([build_number_limiter(0.1, 1000)], suffix="ml/s"),
    "tube_volume": IntType([build_number_limiter(0, 100)], suffix="ml"),
    "consumption_estimation": ChooseOptions.consumption_estimation,
    "carriage_position": IntType([build_number_limiter(0, 100)], suffix="pos"),
}


@dataclass
class DispenserAddonEntry:
    """Registry entry for one custom dispenser extension."""

    name: str
    config_class: type[BasePumpConfig]
    config_fields: dict[str, ConfigInterface[Any]]
    implementation_class: type[BaseDispenser]
    full_config_fields: dict[str, ConfigInterface[Any]] = field(default_factory=dict)


class DispenserExtensionManager:
    """Discovers and registers custom dispenser extensions from addons/dispensers/."""

    def __init__(self) -> None:
        self.dispensers: dict[str, DispenserAddonEntry] = {}
        self._loaded = False

    def _load_all(self) -> None:
        if not DISPENSER_ADDON_FOLDER.exists():
            return
        extension_files = DISPENSER_ADDON_FOLDER.glob("*.py")
        for path in extension_files:
            if path.stem.startswith("__"):
                continue
            self._load_extension(path.stem)

    def _load_extension(self, filename: str) -> None:
        try:
            module = import_module(f"addons.dispensers.{filename}")
        except ImportError as e:
            _logger.error(f"Could not import dispenser extension: {filename} due to <{e}>, {_check_extension}.")
            return

        name: str | None = getattr(module, "EXTENSION_NAME", None)
        if not name:
            _logger.warning(f"Missing EXTENSION_NAME in {filename}, {_check_extension}.")
            return

        config_class = getattr(module, "ConfigClass", None)
        config_fields: dict[str, ConfigInterface[Any]] | None = getattr(module, "CONFIG_FIELDS", None)
        implementation_class = getattr(module, "Implementation", None)

        if config_class is None or config_fields is None or implementation_class is None:
            _logger.warning(
                f"Dispenser extension '{name}' in {filename} is missing ConfigClass, CONFIG_FIELDS, "
                f"or Implementation, {_check_extension}."
            )
            return

        if name in self.dispensers:
            _logger.warning(f"Duplicate dispenser extension name '{name}' in {filename}, skipping.")
            return

        # Validate that Implementation inherits from BaseDispenser

        if not issubclass(implementation_class, BaseDispenser):
            _logger.warning(f"Implementation in '{name}' does not inherit from BaseDispenser, {_check_extension}.")
            return

        # Validate that ConfigClass inherits from BasePumpConfig

        if not issubclass(config_class, BasePumpConfig):
            _logger.warning(f"ConfigClass in '{name}' does not inherit from BasePumpConfig, {_check_extension}.")
            return

        entry = DispenserAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation_class=implementation_class,
        )
        self.dispensers[name] = entry
        _logger.info(f"Loaded dispenser extension: {name}")

    def build_full_config_fields(self) -> None:
        """Build full config fields for all extensions and register them as PUMP_CONFIG variants.

        Must be called before config is read, so the new dispenser types are known.
        """
        if not self._loaded:
            self._load_all()
            self._loaded = True
        if not self.dispensers:
            return

        for name, entry in self.dispensers.items():
            full_fields: dict[str, ConfigInterface[Any]] = {}
            # Add shared base fields first (pump_type comes first in the UI)
            full_fields.update(_SHARED_PUMP_FIELDS)
            # Add user-defined fields after shared ones
            full_fields.update(entry.config_fields)
            entry.full_config_fields = full_fields
            cfg.add_discriminator_variant("PUMP_CONFIG", name, DictType(full_fields, entry.config_class))


def generate_dispenser_extension_skeleton(name: str) -> None:
    """Create a base dispenser extension file under the given name."""
    file_name = name.replace(" ", "_")
    file_name = re.sub(r"\W", "", file_name.lower())
    extension_path = DISPENSER_ADDON_FOLDER / f"{file_name}.py"
    if extension_path.exists():
        msg = f"There is already a dispenser extension created under the {name=} in {file_name}.py"
        typer.echo(typer.style(f"{msg}, aborting...", fg=typer.colors.RED, bold=True))
        raise typer.Exit()
    DISPENSER_ADDON_FOLDER.mkdir(parents=True, exist_ok=True)
    extension_path.write_text(
        (
            DISPENSER_EXTENSION_SKELETON.read_text(encoding="utf-8")
            .replace("EXTENSION_NAME_HOLDER", name)
            .replace("VERSION_HOLDER", __version__)
        ),
        encoding="utf-8",
    )
    msg = f"Dispenser extension file was created at {extension_path}"
    typer.echo(typer.style(msg, fg=typer.colors.GREEN, bold=True))


DISPENSER_ADDONS = DispenserExtensionManager()
