from __future__ import annotations

from typing import Any

from src.config.config_types import ConfigClass, ConfigInterface, StringType
from src.logger_handler import LoggerHandler
from src.programs.addons import BaseHardwareExtension

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is a hardware extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/#hardware-context-extensions
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name for this hardware extension
#   CONFIG_FIELDS  - dict of config fields for GUI configuration
#   ExtensionConfig - config class inheriting from config_types.ConfigClass
#   Implementation - class inheriting from BaseHardwareExtension


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ExtensionConfig(ConfigClass):
    """Custom configuration for this hardware extension.

    Define any attributes your hardware needs.
    """

    label: str

    def __init__(
        self,
        label: str = "default",
        **kwargs: Any,
    ) -> None:
        self.label = label

    def to_config(self) -> dict[str, Any]:
        return {"label": self.label}

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ExtensionConfig:
        return cls(**config)


# Define your config fields here. These will appear in the configuration UI.
CONFIG_FIELDS: dict[str, ConfigInterface] = {
    "label": StringType(default="default"),
}


class MyHardware:
    """Your custom hardware class.

    Rename this and add your own attributes and methods.
    """

    def __init__(self, label: str) -> None:
        self.label = label

    def close(self) -> None:
        """Release any resources (serial ports, connections, etc.)."""


class Implementation(BaseHardwareExtension[ExtensionConfig]):
    """Hardware extension implementation.

    The created object is stored in ``hardware.extra["EXTENSION_NAME_HOLDER"]``
    and can be accessed by your other hardware (dispenser) extensions.
    """

    def create(self, config: ExtensionConfig) -> MyHardware:
        """Create and return your hardware instance.

        This is called once during machine initialization, before dispensers are set up.
        You decide the shape of the return value.
        """
        _logger.info(f"Creating hardware: {config.label}")
        # >>> Initialize your hardware here <<<
        return MyHardware(config.label)

    def cleanup(self, instance: MyHardware) -> None:
        """Clean up the hardware instance.

        Called at program shutdown. Release any resources (serial ports, connections, etc.).
        """
        _logger.info("Cleaning up hardware")
        # >>> Clean up your hardware here <<<
        instance.close()
