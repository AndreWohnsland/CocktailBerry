from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import ConfigClass, ConfigInterface, DictType
from src.logger_handler import LoggerHandler


@dataclass
class BaseAddonEntry:
    """Common fields shared by all extension registry entries."""

    name: str
    config_class: type[ConfigClass]
    config_fields: dict[str, ConfigInterface[Any]]


class BaseExtensionManager[EntryT: BaseAddonEntry](ABC):
    """Shared discovery and loading logic for extension managers.

    Subclasses must define:
      _folder                 - where to find extension .py files
      _import_prefix           - dotted import path prefix (e.g. "addons.hardware")
      _label                  - human-readable label for log messages (e.g. "hardware extension")
      _validate_and_register  - type-specific validation and config entry creation

    Subclasses whose extensions are variants of one discriminated config must also define:
      _config_key             - the config name to register variants under (e.g. "LED_CONFIG")
      _shared_fields          - fields every variant of that config carries
    """

    _folder: Path
    _import_prefix: str
    _label: str
    _config_key: str
    _shared_fields: dict[str, ConfigInterface[Any]]

    def __init__(self) -> None:
        self.entries: dict[str, EntryT] = {}
        self._loaded = False
        self._logger = LoggerHandler(f"{type(self).__name__}")
        self._check_msg = f"please check {self._label} or contact provider"

    def _load_all(self) -> None:
        if not self._folder.exists():
            return
        for path in self._folder.glob("*.py"):
            if path.stem.startswith("__"):
                continue
            self._load_extension(path.stem)

    def _load_extension(self, filename: str) -> None:
        try:
            module = import_module(f"{self._import_prefix}.{filename}")
        except ImportError as e:
            self._logger.error(f"Could not import {self._label}: {filename} due to <{e}>, {self._check_msg}.")
            return

        name: str | None = getattr(module, "EXTENSION_NAME", None)
        if not name:
            self._logger.warning(f"Missing EXTENSION_NAME in {filename}, {self._check_msg}.")
            return

        config_class = getattr(module, "ExtensionConfig", None)
        config_fields: dict[str, ConfigInterface[Any]] | None = getattr(module, "CONFIG_FIELDS", None)
        implementation_class = getattr(module, "Implementation", None)

        if config_class is None or config_fields is None or implementation_class is None:
            self._logger.warning(
                f"{self._label.capitalize()} '{name}' in {filename} is missing ExtensionConfig, "
                "CONFIG_FIELDS, "
                f"or Implementation, {self._check_msg}."
            )
            return

        if name in self.entries:
            self._logger.warning(f"Duplicate {self._label} name '{name}' in {filename}, skipping.")
            return

        self._validate_and_register(name, config_class, config_fields, implementation_class)

    @abstractmethod
    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        """Validate type-specific base classes and create the registry entry."""

    def build_full_config_fields(self) -> None:
        """Register every discovered extension as a variant of ``_config_key``.

        Must be called before the config is read, so the new types are known.
        """
        self._ensure_loaded()
        for name, entry in self.entries.items():
            # shared fields first, so the discriminating *_type field leads the UI
            full_fields = {**self._shared_fields, **entry.config_fields}
            cfg.add_discriminator_variant(self._config_key, name, DictType(full_fields, entry.config_class))

    def _ensure_loaded(self) -> None:
        """Run discovery once, then mark as loaded."""
        if not self._loaded:
            self._load_all()
            self._loaded = True
