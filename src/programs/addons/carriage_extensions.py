from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import SHARED_CARRIAGE_FIELDS
from src.config.config_types import BaseCarriageConfig, ConfigInterface
from src.filepath import CARRIAGE_ADDON_FOLDER
from src.machine.carriage.base import CarriageInterface
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager


@dataclass
class CarriageAddonEntry(BaseAddonEntry):
    """Registry entry for one custom carriage extension."""

    config_class: type[BaseCarriageConfig]
    implementation_class: type[CarriageInterface]


class CarriageExtensionManager(BaseExtensionManager[CarriageAddonEntry]):
    """Discovers and registers custom carriage extensions from addons/carriages/."""

    _folder = CARRIAGE_ADDON_FOLDER
    _import_prefix = "addons.carriages"
    _label = "carriage extension"
    _config_key = "CARRIAGE_CONFIG"
    _shared_fields = SHARED_CARRIAGE_FIELDS

    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        if not issubclass(implementation_class, CarriageInterface):
            self._logger.warning(
                f"Implementation in '{name}' does not inherit from CarriageInterface, {self._check_msg}."
            )
            return

        if not issubclass(config_class, BaseCarriageConfig):
            self._logger.warning(
                f"ExtensionConfig in '{name}' does not inherit from BaseCarriageConfig, {self._check_msg}."
            )
            return

        self.entries[name] = CarriageAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation_class=implementation_class,
        )
        self._logger.info(f"Loaded carriage extension: {name}")


CARRIAGE_ADDONS = CarriageExtensionManager()
