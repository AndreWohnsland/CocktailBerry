"""Factory for creating I2C expander devices and GPIO controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src import I2CExpanderType
from src.config.config_types import I2CExpanderConfig
from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import get_i2c
from src.machine.i2c.MCP23017 import MCP23017GPIO, get_mcp23017
from src.machine.i2c.PCA9535 import PCA9535, PCA9535GPIO, get_pca9535
from src.machine.i2c.PCF8574 import PCF8574GPIO, get_pcf8574
from src.machine.interface import SinglePinController

if TYPE_CHECKING:
    from adafruit_mcp230xx.mcp23017 import MCP23017
    from adafruit_pcf8574 import PCF8574


_logger = LoggerHandler("I2CExpanderFactory")


class I2CExpanderFactory:
    """Factory for managing I2C expander devices and creating GPIO controllers.

    Takes a list of I2CExpanderConfig and manages device instances internally.
    Provides create_i2c_gpio() to create GPIO controllers for specific device types.
    """

    def __init__(self, configs: list[I2CExpanderConfig]) -> None:
        self._configs = configs
        self._i2c = None
        self._mcp23017: MCP23017 | None = None
        self._pcf8574: PCF8574 | None = None
        self._pca9535: PCA9535 | None = None
        self._initialize_devices()

    def _initialize_devices(self) -> None:
        """Initialize I2C bus and devices based on enabled configs."""
        # Check if any config is enabled
        enabled_configs = [c for c in self._configs if c.enabled]
        if not enabled_configs:
            _logger.debug("No I2C expanders enabled")
            return

        # Initialize I2C bus
        self._i2c = get_i2c()
        if self._i2c is None:
            return

        # Initialize each enabled device
        for config in enabled_configs:
            device_type = config.device_type
            match device_type:
                case "MCP23017":
                    if self._mcp23017 is not None:
                        _logger.warning("Duplicate MCP23017 config found, using first one")
                        continue
                    self._mcp23017 = get_mcp23017(config, self._i2c)
                case "PCF8574":
                    if self._pcf8574 is not None:
                        _logger.warning("Duplicate PCF8574 config found, using first one")
                        continue
                    self._pcf8574 = get_pcf8574(config, self._i2c)
                case "PCA9535":
                    if self._pca9535 is not None:
                        _logger.warning("Duplicate PCA9535 config found, using first one")
                        continue
                    self._pca9535 = get_pca9535(config, self._i2c)

    def get_config_for_type(self, device_type: I2CExpanderType) -> I2CExpanderConfig | None:
        """Get the config for a specific device type."""
        for config in self._configs:
            if config.device_type == device_type and config.enabled:
                return config
        return None

    def create_i2c_gpio(
        self,
        device_type: I2CExpanderType,
        pin: int,
        invert_override: bool | None = None,
    ) -> SinglePinController:
        """Create a GPIO controller for the specified I2C expander type.

        Args:
            device_type: The type of I2C expander (MCP23017, PCF8574, PCA9535)
            pin: The pin number on the expander
            invert_override: Optional override for pin inversion. If None, uses config value.

        Returns:
            A SinglePinController for the specified pin.

        """
        config = self.get_config_for_type(device_type)
        inverted = invert_override if invert_override is not None else (config.inverted if config else False)

        if config is None:
            _logger.error(f"No enabled config found for device type {device_type}, please check your configuration.")

        match device_type:
            case "MCP23017":
                return MCP23017GPIO(pin, inverted, self._mcp23017)
            case "PCF8574":
                return PCF8574GPIO(pin, inverted, self._pcf8574)
            case "PCA9535":
                return PCA9535GPIO(pin, inverted, self._pca9535)

    @property
    def has_enabled_devices(self) -> bool:
        """Check if any I2C expander is enabled and initialized."""
        return self._mcp23017 is not None or self._pcf8574 is not None or self._pca9535 is not None
