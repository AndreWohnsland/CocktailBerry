from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import SHARED_PUMP_FIELDS
from src.config.config_types import BasePumpConfig, ConfigInterface
from src.filepath import DISPENSER_ADDON_FOLDER
from src.machine.dispensers.base import BaseDispenser
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager


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
    _config_key = "PUMP_CONFIG"
    _shared_fields = SHARED_PUMP_FIELDS

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


DISPENSER_ADDONS = DispenserExtensionManager()
