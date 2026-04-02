from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import get_i2c
from src.machine.scale.base import ScaleInterface

_logger = LoggerHandler("NAU7802Scale")

try:
    from cedargrove_nau7802 import NAU7802  # type: ignore[import-untyped]

    NAU7802_AVAILABLE = True
except (ModuleNotFoundError, ImportError, RuntimeError):
    NAU7802_AVAILABLE = False


class NAU7802Scale(ScaleInterface):
    """Scale using NAU7802 I2C load cell amplifier."""

    def __init__(self, i2c_address: int, calibration_factor: float) -> None:
        if not NAU7802_AVAILABLE:
            msg = "cedargrove_nau7802 library is not available. Cannot initialize NAU7802 scale."
            _logger.error(msg)
            raise ImportError(msg)
        self._calibration_factor = calibration_factor
        self._zero_offset: float = 0.0
        i2c = get_i2c()
        if i2c is None:
            msg = "I2C bus is not available. Cannot initialize NAU7802 scale."
            _logger.error(msg)
            raise RuntimeError(msg)
        self._nau = NAU7802(i2c, address=i2c_address)
        self._nau.gain = 128
        self._nau.channel = 1
        _logger.log_event("INFO", f"NAU7802 scale initialized (address=0x{i2c_address:02X})")

    def _raw_reading(self) -> float:
        readings = [self._nau.read() for _ in range(5)]
        return sum(readings) / len(readings)

    def tare(self) -> None:
        self._zero_offset = self._raw_reading()

    def read_grams(self) -> float:
        return (self._raw_reading() - self._zero_offset) / self._calibration_factor

    def read_raw(self) -> float:
        return self._raw_reading() - self._zero_offset

    def cleanup(self) -> None:
        self._nau.enable = False
