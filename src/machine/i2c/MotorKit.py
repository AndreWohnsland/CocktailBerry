from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import get_i2c

try:
    from adafruit_motorkit import MotorKit

    MODULE_AVAILABLE = True
except (ModuleNotFoundError, RuntimeError):
    MODULE_AVAILABLE = False

_logger = LoggerHandler("MotorKit")

# allow None since we might not be able to initialize the MotorKit board
_motorkit_boards: dict[int, MotorKit | None] = {}
"""Module-level cache of address -> MotorKit instance, shared across all dispensers."""


def get_motorkit(address: int) -> MotorKit | None:
    """Return the MotorKit instance for the given I2C address, creating it if needed.

    Subsequent calls with the same address return the cached instance without
    reinitialising the hardware.
    """
    if address in _motorkit_boards:
        return _motorkit_boards[address]
    _motorkit_boards[address] = create_motorkit(address)
    return _motorkit_boards[address]


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
