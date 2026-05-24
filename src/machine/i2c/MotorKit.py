from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import get_i2c

try:
    from adafruit_motorkit import MotorKit

    MODULE_AVAILABLE = True
except (ModuleNotFoundError, RuntimeError):
    MODULE_AVAILABLE = False

_logger = LoggerHandler("MotorKit")


def create_motorkit(address: int) -> MotorKit | None:
    """Create and return a new MotorKit instance at the given I2C address.

    Returns ``None`` if the module is unavailable or the hardware cannot be reached.
    """
    if not MODULE_AVAILABLE:
        _logger.warning("adafruit_motorkit is not available. Cannot control MotorKit boards.")
        return None
    i2c = get_i2c()
    if i2c is None:
        return None
    try:
        kit = MotorKit(i2c=i2c, address=address)
        _logger.info(f"Initialized MotorKit at address 0x{address:02x}")
    except Exception as e:
        _logger.error(f"Could not initialize MotorKit at 0x{address:02x}: {e}")
        return None
    return kit
