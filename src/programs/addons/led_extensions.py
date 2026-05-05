from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import SHARED_LED_FIELDS
from src.config.config_types import BaseLedConfig, ConfigInterface, DictType
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

    def build_full_config_fields(self) -> None:
        """Build full config fields for all extensions and register them as LED_CONFIG variants.

        Must be called before config is read, so the new led types are known.
        """
        self._ensure_loaded()
        if not self.entries:
            return

        for name, entry in self.entries.items():
            full_fields: dict[str, ConfigInterface[Any]] = {}
            # Add shared base fields first (led_type comes first in the UI)
            full_fields.update(SHARED_LED_FIELDS)
            # Add user-defined fields after shared ones
            full_fields.update(entry.config_fields)
            cfg.add_discriminator_variant("LED_CONFIG", name, DictType(full_fields, entry.config_class))


LED_ADDONS = LedExtensionManager()
