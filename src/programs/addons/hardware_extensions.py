from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import ConfigClass, ConfigInterface, DictType
from src.filepath import HARDWARE_ADDON_FOLDER
from src.programs.addons import BaseHardwareExtension
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager


@dataclass
class HardwareAddonEntry(BaseAddonEntry):
    """Registry entry for one custom hardware extension."""

    config_class: type[ConfigClass]
    implementation: BaseHardwareExtension[Any]
    instance: Any = field(default=None)


class HardwareExtensionManager(BaseExtensionManager[HardwareAddonEntry]):
    """Discovers and registers custom hardware extensions from addons/hardware/."""

    _folder = HARDWARE_ADDON_FOLDER
    _import_prefix = "addons.hardware"
    _label = "hardware extension"

    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        if not isinstance(implementation_class, type) or not issubclass(implementation_class, BaseHardwareExtension):
            self._logger.warning(
                f"Implementation in '{name}' does not inherit from BaseHardwareExtension, {self._check_msg}."
            )
            return

        if not isinstance(config_class, type) or not issubclass(config_class, ConfigClass):
            self._logger.warning(f"ExtensionConfig in '{name}' does not inherit from ConfigClass, {self._check_msg}.")
            return

        self.entries[name] = HardwareAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation=implementation_class(),
        )
        self._logger.info(f"Loaded hardware extension: {name}")

    def build_config(self) -> None:
        """Discover extensions and register their config fields.

        Must be called before config is read, so the new hardware configs are known.
        Each hardware extension gets its own top-level config entry named after the extension.
        """
        self._ensure_loaded()
        if not self.entries:
            return

        for name, entry in self.entries.items():
            config_name = f"HW_{name.upper().replace(' ', '_')}"
            cfg.add_complex_config(config_name, DictType(entry.config_fields, entry.config_class))

    def create_all(self) -> dict[str, Any]:
        """Create all hardware extension instances from their loaded configs.

        Returns a dict mapping extension name -> instance for HardwareContext.extra.
        """
        result: dict[str, Any] = {}
        for name, entry in self.entries.items():
            config_name = f"HW_{name.upper().replace(' ', '_')}"
            config = getattr(cfg, config_name, None)
            if config is None:
                self._logger.warning(f"Config for hardware extension '{name}' not found, skipping.")
                continue
            try:
                instance = entry.implementation.create(config)
                entry.instance = instance
                result[name] = instance
                self._logger.info(f"Created hardware extension instance: {name}")
            except Exception as e:
                self._logger.error(f"Failed to create hardware extension '{name}': {e}")
        return result

    def cleanup_all(self) -> None:
        """Clean up all hardware extension instances."""
        for name, entry in self.entries.items():
            if entry.instance is not None:
                try:
                    entry.implementation.cleanup(entry.instance)
                    self._logger.info(f"Cleaned up hardware extension: {name}")
                except Exception as e:
                    self._logger.error(f"Failed to cleanup hardware extension '{name}': {e}")
                entry.instance = None


HARDWARE_ADDONS = HardwareExtensionManager()
