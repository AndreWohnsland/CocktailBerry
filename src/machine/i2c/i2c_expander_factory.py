"""Factory for creating I2C expander devices and GPIO controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src import I2CExpanderType
from src.config.config_types import I2CExpanderConfig, PinId
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
    Supports multiple boards of the same type, distinguished by board_number.
    Provides create_i2c_gpio() to create GPIO controllers for specific device types.
    """

    def __init__(self, configs: list[I2CExpanderConfig]) -> None:
        self._configs = configs
        self._i2c = None
        self._mcp23017: dict[int, MCP23017] = {}
        self._pcf8574: dict[int, PCF8574] = {}
        self._pca9535: dict[int, PCA9535] = {}
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
            board_number = config.board_number
            match device_type:
                case "MCP23017":
                    device = get_mcp23017(config, self._i2c)
                    if device is not None:
                        self._mcp23017[board_number] = device
                case "PCF8574":
                    device = get_pcf8574(config, self._i2c)
                    if device is not None:
                        self._pcf8574[board_number] = device
                case "PCA9535":
                    device = get_pca9535(config, self._i2c)
                    if device is not None:
                        self._pca9535[board_number] = device

    def get_config_for_type(self, device_type: I2CExpanderType, board_number: int = 1) -> I2CExpanderConfig | None:
        """Get the config for a specific device type and board number."""
        for config in self._configs:
            if config.device_type == device_type and config.board_number == board_number and config.enabled:
                return config
        return None

    def create_i2c_gpio(
        self,
        pin_id: PinId,
        invert_override: bool | None = None,
    ) -> SinglePinController:
        """Create a GPIO controller for the specified I2C expander type and board.

        Args:
            pin_id: The PinId identifying the device type, board number, and pin.
            invert_override: Optional override for pin inversion. If None, uses config value.

        Returns:
            A SinglePinController for the specified pin.

        """
        device_type = cast(I2CExpanderType, pin_id.pin_type)  # only called for I2C types
        board_number = pin_id.board_number
        pin = pin_id.pin
        config = self.get_config_for_type(device_type, board_number)
        default_inverted = config.inverted if config else False
        inverted = invert_override if invert_override is not None else default_inverted

        if config is None:
            _logger.error(
                f"No enabled config found for device type {device_type} board {board_number}, "
                "please check your configuration."
            )

        match device_type:
            case "MCP23017":
                return MCP23017GPIO(pin, inverted, self._mcp23017.get(board_number))
            case "PCF8574":
                return PCF8574GPIO(pin, inverted, self._pcf8574.get(board_number))
            case "PCA9535":
                return PCA9535GPIO(pin, inverted, self._pca9535.get(board_number))
            case _:
                msg = f"Unsupported I2C device type: {device_type}"
                raise ValueError(msg)

    @property
    def has_enabled_devices(self) -> bool:
        """Check if any I2C expander is enabled and initialized."""
        return bool(self._mcp23017 or self._pcf8574 or self._pca9535)
