from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import ConfigClass, ConfigInterface, DictType
from src.filepath import HARDWARE_ADDON_FOLDER
from src.logger_handler import LoggerHandler
from src.programs.addons import BaseHardwareExtension

_logger = LoggerHandler("HardwareExtensionManager")
_check_extension = "please check hardware extension or contact provider"


@dataclass
class HardwareAddonEntry:
    """Registry entry for one custom hardware extension."""

    name: str
    config_class: type[ConfigClass]
    config_fields: dict[str, ConfigInterface[Any]]
    implementation: BaseHardwareExtension[Any]
    instance: Any = field(default=None)


class HardwareExtensionManager:
    """Discovers and registers custom hardware extensions from addons/hardware/."""

    def __init__(self) -> None:
        self.hardware: dict[str, HardwareAddonEntry] = {}
        self._loaded = False

    def _load_all(self) -> None:
        if not HARDWARE_ADDON_FOLDER.exists():
            return
        extension_files = HARDWARE_ADDON_FOLDER.glob("*.py")
        for path in extension_files:
            if path.stem.startswith("__"):
                continue
            self._load_extension(path.stem)

    def _load_extension(self, filename: str) -> None:
        try:
            module = import_module(f"addons.hardware.{filename}")
        except ImportError as e:
            _logger.error(f"Could not import hardware extension: {filename} due to <{e}>, {_check_extension}.")
            return

        name: str | None = getattr(module, "EXTENSION_NAME", None)
        if not name:
            _logger.warning(f"Missing EXTENSION_NAME in {filename}, {_check_extension}.")
            return

        config_class = getattr(module, "ExtensionConfig", None)
        config_fields: dict[str, ConfigInterface[Any]] | None = getattr(module, "CONFIG_FIELDS", None)
        implementation_class = getattr(module, "Implementation", None)

        if config_class is None or config_fields is None or implementation_class is None:
            _logger.warning(
                f"Hardware extension '{name}' in {filename} is missing ExtensionConfig, "
                "CONFIG_FIELDS, "
                f"or Implementation, {_check_extension}."
            )
            return

        if name in self.hardware:
            _logger.warning(f"Duplicate hardware extension name '{name}' in {filename}, skipping.")
            return

        if not isinstance(config_class, type) or not issubclass(config_class, ConfigClass):
            _logger.warning(f"ExtensionConfig in '{name}' does not inherit from ConfigClass, {_check_extension}.")
            return

        if not isinstance(implementation_class, type) or not issubclass(implementation_class, BaseHardwareExtension):
            _logger.warning(
                f"Implementation in '{name}' does not inherit from BaseHardwareExtension, {_check_extension}."
            )
            return

        entry = HardwareAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation=implementation_class(),
        )
        self.hardware[name] = entry
        _logger.info(f"Loaded hardware extension: {name}")

    def build_config(self) -> None:
        """Discover extensions and register their config fields.

        Must be called before config is read, so the new hardware configs are known.
        Each hardware extension gets its own top-level config entry named after the extension.
        """
        if not self._loaded:
            self._load_all()
            self._loaded = True
        if not self.hardware:
            return

        for name, entry in self.hardware.items():
            config_name = f"HW_{name.upper().replace(' ', '_')}"
            cfg.add_complex_config(config_name, DictType(entry.config_fields, entry.config_class))

    def create_all(self) -> dict[str, Any]:
        """Create all hardware extension instances from their loaded configs.

        Returns a dict mapping extension name -> instance for HardwareContext.extra.
        """
        result: dict[str, Any] = {}
        for name, entry in self.hardware.items():
            config_name = f"HW_{name.upper().replace(' ', '_')}"
            config = getattr(cfg, config_name, None)
            if config is None:
                _logger.warning(f"Config for hardware extension '{name}' not found, skipping.")
                continue
            try:
                instance = entry.implementation.create(config)
                entry.instance = instance
                result[name] = instance
                _logger.info(f"Created hardware extension instance: {name}")
            except Exception as e:
                _logger.error(f"Failed to create hardware extension '{name}': {e}")
        return result

    def cleanup_all(self) -> None:
        """Clean up all hardware extension instances."""
        for name, entry in self.hardware.items():
            if entry.instance is not None:
                try:
                    entry.implementation.cleanup(entry.instance)
                    _logger.info(f"Cleaned up hardware extension: {name}")
                except Exception as e:
                    _logger.error(f"Failed to cleanup hardware extension '{name}': {e}")
                entry.instance = None


HARDWARE_ADDONS = HardwareExtensionManager()
