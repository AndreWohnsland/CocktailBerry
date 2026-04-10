from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import BasePumpConfig, ChooseOptions, ConfigInterface, DictType, FloatType, IntType
from src.config.validators import build_number_limiter
from src.filepath import DISPENSER_ADDON_FOLDER
from src.machine.dispensers.base import BaseDispenser
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager

# Shared BasePumpConfig fields auto-injected into every dispenser extension.
_SHARED_PUMP_FIELDS: dict[str, ConfigInterface[Any]] = {
    "pump_type": ChooseOptions.dispenser,
    "volume_flow": FloatType([build_number_limiter(0.1, 1000)], suffix="ml/s"),
    "tube_volume": IntType([build_number_limiter(0, 100)], suffix="ml"),
    "consumption_estimation": ChooseOptions.consumption_estimation,
    "carriage_position": IntType([build_number_limiter(0, 100)], suffix="pos"),
}


@dataclass
class DispenserAddonEntry(BaseAddonEntry):
    """Registry entry for one custom dispenser extension."""

    config_class: type[BasePumpConfig]
    implementation_class: type[BaseDispenser]


class DispenserExtensionManager(BaseExtensionManager[DispenserAddonEntry]):
    """Discovers and registers custom dispenser extensions from addons/dispensers/."""

    _folder = DISPENSER_ADDON_FOLDER
    _import_prefix = "addons.dispensers"
    _label = "dispenser extension"

    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        if not issubclass(implementation_class, BaseDispenser):
            self._logger.warning(f"Implementation in '{name}' does not inherit from BaseDispenser, {self._check_msg}.")
            return

        if not issubclass(config_class, BasePumpConfig):
            self._logger.warning(
                f"ExtensionConfig in '{name}' does not inherit from BasePumpConfig, {self._check_msg}."
            )
            return

        self.entries[name] = DispenserAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation_class=implementation_class,
        )
        self._logger.info(f"Loaded dispenser extension: {name}")

    def build_full_config_fields(self) -> None:
        """Build full config fields for all extensions and register them as PUMP_CONFIG variants.

        Must be called before config is read, so the new dispenser types are known.
        """
        self._ensure_loaded()
        if not self.entries:
            return

        for name, entry in self.entries.items():
            full_fields: dict[str, ConfigInterface[Any]] = {}
            # Add shared base fields first (pump_type comes first in the UI)
            full_fields.update(_SHARED_PUMP_FIELDS)
            # Add user-defined fields after shared ones
            full_fields.update(entry.config_fields)
            cfg.add_discriminator_variant("PUMP_CONFIG", name, DictType(full_fields, entry.config_class))


DISPENSER_ADDONS = DispenserExtensionManager()
