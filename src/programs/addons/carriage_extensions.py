from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import SHARED_CARRIAGE_FIELDS
from src.config.config_types import BaseCarriageConfig, ConfigInterface, DictType
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

    def build_full_config_fields(self) -> None:
        """Build full config fields for all extensions and register them as CARRIAGE_CONFIG variants.

        Must be called before config is read, so the new carriage types are known.
        """
        self._ensure_loaded()
        if not self.entries:
            return

        for name, entry in self.entries.items():
            full_fields: dict[str, ConfigInterface[Any]] = {}
            # Add shared base fields first (carriage_type comes first in the UI)
            full_fields.update(SHARED_CARRIAGE_FIELDS)
            # Add user-defined fields after shared ones
            full_fields.update(entry.config_fields)
            cfg.add_discriminator_variant("CARRIAGE_CONFIG", name, DictType(full_fields, entry.config_class))


CARRIAGE_ADDONS = CarriageExtensionManager()
