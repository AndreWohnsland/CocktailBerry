from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_manager import SHARED_SCALE_FIELDS
from src.config.config_types import BaseScaleConfig, ConfigInterface
from src.filepath import SCALE_ADDON_FOLDER
from src.machine.scale.base import ScaleInterface
from src.programs.addons.extension_base import BaseAddonEntry, BaseExtensionManager


@dataclass
class ScaleAddonEntry(BaseAddonEntry):
    """Registry entry for one custom scale extension."""

    config_class: type[BaseScaleConfig]
    implementation_class: type[ScaleInterface]


class ScaleExtensionManager(BaseExtensionManager[ScaleAddonEntry]):
    """Discovers and registers custom scale extensions from addons/scales/."""

    _folder = SCALE_ADDON_FOLDER
    _import_prefix = "addons.scales"
    _label = "scale extension"
    _config_key = "SCALE_CONFIG"
    _shared_fields = SHARED_SCALE_FIELDS

    def _validate_and_register(
        self,
        name: str,
        config_class: type,
        config_fields: dict[str, ConfigInterface[Any]],
        implementation_class: type,
    ) -> None:
        if not issubclass(implementation_class, ScaleInterface):
            self._logger.warning(f"Implementation in '{name}' does not inherit from ScaleInterface, {self._check_msg}.")
            return

        if not issubclass(config_class, BaseScaleConfig):
            self._logger.warning(
                f"ExtensionConfig in '{name}' does not inherit from BaseScaleConfig, {self._check_msg}."
            )
            return

        self.entries[name] = ScaleAddonEntry(
            name=name,
            config_class=config_class,
            config_fields=config_fields,
            implementation_class=implementation_class,
        )
        self._logger.info(f"Loaded scale extension: {name}")


SCALE_ADDONS = ScaleExtensionManager()
