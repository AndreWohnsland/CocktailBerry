from __future__ import annotations

from typing import Any

from src.config.config_types import ConfigClass as BaseConfigClass
from src.config.config_types import StringType
from src.logger_handler import LoggerHandler

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is a hardware extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name for this hardware extension
#   CONFIG_FIELDS  - dict of config fields for GUI configuration
#   ExtensionConfig - config class inheriting from config_types.ConfigClass
#   create         - function that creates the hardware instance from config
#   cleanup        - function that cleans up the hardware instance


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ExtensionConfig(BaseConfigClass):
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
CONFIG_FIELDS: dict[str, Any] = {
    "label": StringType(default="default"),
}


def create(config: ExtensionConfig) -> Any:
    """Create and return your hardware instance.

    This is called once during machine initialization, before dispensers are set up.
    The returned object is stored in ``hardware.extra["EXTENSION_NAME_HOLDER"]``
    and can be accessed by your dispenser extensions.

    You decide the shape of the return value — it can be a single object,
    a list, a dict, or anything your dispenser code expects.
    """
    _logger.info(f"Creating hardware: {config.label}")
    # >>> Initialize your hardware here <<<
    # Example: return MyUartBoard(config.port, config.baud_rate)
    return None


def cleanup(instance: Any) -> None:
    """Clean up the hardware instance.

    Called at program shutdown. Release any resources (serial ports, connections, etc.).
    """
    _logger.info("Cleaning up hardware")
    # >>> Clean up your hardware here <<<
