from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import SHARED_RFID_FIELDS
from src.config.config_types import BaseRfidConfig, ConfigInterface, DictType
from src.filepath import RFID_ADDON_FOLDER
from src.machine.rfid.base import RFIDInterface
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager


@dataclass
class RfidAddonEntry(BaseAddonEntry):
    """Registry entry for one custom RFID extension."""

    config_class: type[BaseRfidConfig]
    implementation_class: type[RFIDInterface]


class RfidExtensionManager(BaseExtensionManager[RfidAddonEntry]):
    """Discovers and registers custom RFID extensions from addons/rfid/."""

    _folder = RFID_ADDON_FOLDER
    _import_prefix = "addons.rfid"
    _label = "rfid extension"

    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        if not issubclass(implementation_class, RFIDInterface):
            self._logger.warning(f"Implementation in '{name}' does not inherit from RFIDInterface, {self._check_msg}.")
            return

        if not issubclass(config_class, BaseRfidConfig):
            self._logger.warning(
                f"ExtensionConfig in '{name}' does not inherit from BaseRfidConfig, {self._check_msg}."
            )
            return

        self.entries[name] = RfidAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation_class=implementation_class,
        )
        self._logger.info(f"Loaded rfid extension: {name}")

    def build_full_config_fields(self) -> None:
        """Build full config fields for all extensions and register them as RFID_CONFIG variants.

        Must be called before config is read, so the new rfid types are known.
        """
        self._ensure_loaded()
        if not self.entries:
            return

        for name, entry in self.entries.items():
            full_fields: dict[str, ConfigInterface[Any]] = {}
            # Add shared base fields first (rfid_type comes first in the UI)
            full_fields.update(SHARED_RFID_FIELDS)
            # Add user-defined fields after shared ones
            full_fields.update(entry.config_fields)
            cfg.add_discriminator_variant("RFID_CONFIG", name, DictType(full_fields, entry.config_class))


RFID_ADDONS = RfidExtensionManager()
