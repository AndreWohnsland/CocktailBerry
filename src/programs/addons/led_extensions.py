from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import SHARED_LED_FIELDS
from src.config.config_types import BaseLedConfig, ConfigInterface
from src.filepath import LED_ADDON_FOLDER
from src.machine.leds.base import LedInterface
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager


@dataclass
class LedAddonEntry(BaseAddonEntry):
    """Registry entry for one custom LED extension."""

    config_class: type[BaseLedConfig]
    implementation_class: type[LedInterface]


class LedExtensionManager(BaseExtensionManager[LedAddonEntry]):
    """Discovers and registers custom LED extensions from addons/leds/."""

    _folder = LED_ADDON_FOLDER
    _import_prefix = "addons.leds"
    _label = "led extension"
    _config_key = "LED_CONFIG"
    _shared_fields = SHARED_LED_FIELDS

    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        if not issubclass(implementation_class, LedInterface):
            self._logger.warning(f"Implementation in '{name}' does not inherit from LedInterface, {self._check_msg}.")
            return

        if not issubclass(config_class, BaseLedConfig):
            self._logger.warning(f"ExtensionConfig in '{name}' does not inherit from BaseLedConfig, {self._check_msg}.")
            return

        self.entries[name] = LedAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation_class=implementation_class,
        )
        self._logger.info(f"Loaded led extension: {name}")


LED_ADDONS = LedExtensionManager()
