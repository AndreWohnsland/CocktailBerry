from __future__ import annotations

from typing import TYPE_CHECKING

from src.config.config_types import I2CExpanderConfig
from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import MODULE_AVAILABLE, I2CExpanderGPIO, get_i2c_device

try:
    from adafruit_mcp230xx.mcp23017 import MCP23017

    MODULE_AVAILABLE = True
except (ModuleNotFoundError, RuntimeError):
    MODULE_AVAILABLE = False

if TYPE_CHECKING:
    import busio

_logger = LoggerHandler("MCP23017")


def MCP23017GPIO(pin: int, inverted: bool, device: MCP23017 | None) -> I2CExpanderGPIO:
    """Create an I2CExpanderGPIO for an MCP23017 device."""
    return I2CExpanderGPIO(pin, inverted, device, "MCP23017")


def get_mcp23017(config: I2CExpanderConfig, i2c: busio.I2C | None) -> MCP23017 | None:
    """Get or create an MCP23017 device at the given address."""
    if not MODULE_AVAILABLE:
        _logger.debug("MCP23017 module not available")
        return None
    return get_i2c_device(config, i2c, MCP23017, "MCP23017")
