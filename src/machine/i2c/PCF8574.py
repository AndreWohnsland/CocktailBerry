from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler

try:
    from adafruit_pcf8574 import PCF8574

    MODULE_AVAILABLE = True
except (ModuleNotFoundError, RuntimeError):
    MODULE_AVAILABLE = False

from src.config.config_types import I2CExpanderConfig
from src.machine.i2c.i2c_expander import I2CExpanderGPIO, get_i2c_device

if TYPE_CHECKING:
    import busio

_logger = LoggerHandler("PCF8574")


def PCF8574GPIO(pin: int, inverted: bool, device: PCF8574 | None) -> I2CExpanderGPIO:
    """Create an I2CExpanderGPIO for a PCF8574 device."""
    return I2CExpanderGPIO(pin, inverted, device, "PCF8574")


def get_pcf8574(config: I2CExpanderConfig, i2c: busio.I2C | None) -> PCF8574 | None:
    """Get or create a PCF8574 device at the given address."""
    if not MODULE_AVAILABLE:
        _logger.debug("PCF8574 module not available")
        return None
    return get_i2c_device(config, i2c, PCF8574, "PCF8574")
