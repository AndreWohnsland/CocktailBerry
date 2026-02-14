from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from src.config.config_types import I2CExpanderConfig
from src.machine.interface import SinglePinController

try:
    import board
    import busio
    from digitalio import Pull

    MODULE_AVAILABLE = True
except (ModuleNotFoundError, RuntimeError):
    MODULE_AVAILABLE = False

if TYPE_CHECKING:
    from adafruit_mcp230xx.digital_inout import DigitalInOut as MCP23017DigitalInOut
    from adafruit_mcp230xx.mcp23017 import MCP23017
    from adafruit_pcf8574 import PCF8574
    from adafruit_pcf8574 import DigitalInOut as PCF8574DigitalInOut

from src.logger_handler import LoggerHandler

_logger = LoggerHandler("I2CExpander")


class I2CExpanderGPIO(SinglePinController):
    """Generic GPIO controller for I2C expander devices.

    Works with any device implementing the DigitalInOut interface (usually adafruit)
    (e.g. MCP23017, PCF8574). Both use an identical pin interface
    (get_pin -> DigitalInOut with .value, .switch_to_input, .switch_to_output).
    """

    def __init__(
        self,
        pin: int,
        inverted: bool,
        device: MCP23017 | PCF8574 | None,
        device_name: str,
    ) -> None:
        self.high = True
        self.low = False
        if inverted:
            self.high, self.low = self.low, self.high
        self.pin = pin
        self._device = device
        self._device_name = device_name
        self._controller: MCP23017DigitalInOut | PCF8574DigitalInOut | None = None

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the I2C expander pin."""
        if self._device is None:
            _logger.warning(f"No device found. Will not be able to control pin: {self._device_name}-{self.pin}")
            return

        try:
            pin = self._device.get_pin(self.pin)
            if is_input:
                pull = Pull.DOWN if pull_down else Pull.UP
                pin.switch_to_input(pull=pull)  # ty:ignore[invalid-argument-type]
            else:
                pin.switch_to_output(value=self.low)
            self._controller = pin
            _logger.debug(f"Initialized {self._device_name} pin {self.pin} as {'input' if is_input else 'output'}")
        except Exception as e:
            _logger.error(f"Could not initialize {self._device_name} pin {self.pin}: {e}")

    def activate(self) -> None:
        if self._controller is None:
            return
        self._controller.value = self.high

    def close(self) -> None:
        if self._controller is None:
            return
        self._controller.value = self.low

    def cleanup(self) -> None:
        self.close()

    def read(self) -> bool:
        if self._controller is None:
            return False
        return self._controller.value


def get_i2c_device[T](
    config: I2CExpanderConfig,
    i2c: busio.I2C | None,
    constructor: Callable[..., T],
    name: str,
) -> T | None:
    if not config.enabled:
        return None
    if i2c is None:
        _logger.error(f"Cannot get {name} device without I2C bus")
        return None
    try:
        device = constructor(i2c, address=config.address_hex)
        _logger.info(f"Initialized {name} at address 0x{config.address_hex:02x}")
    except Exception as e:
        _logger.error(f"Could not initialize {name} at 0x{config.address_hex:02x}: {e}")
        return None
    return device


def get_i2c() -> busio.I2C | None:
    """Get or create the I2C bus.

    Returns:
        The I2C bus instance, or None if initialization fails.

    """
    if not MODULE_AVAILABLE:
        _logger.warning(
            "I2C dependencies not available. Cannot control I2C (MCP23017, PCF8574, PCA9535) expanders/devices."
        )
        return None
    try:
        return busio.I2C(board.SCL, board.SDA)  # ty:ignore[possibly-missing-attribute]
    except Exception as e:
        _logger.error(f"Could not initialize I2C bus: {e}")
        return None
