from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import get_i2c
from src.machine.scale.base import ScaleInterface

if TYPE_CHECKING:
    from src.config.config_types import NAU7802ScaleConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("NAU7802Scale")

try:
    from cedargrove_nau7802 import NAU7802  # type: ignore[import-untyped]

    NAU7802_AVAILABLE = True
except (ModuleNotFoundError, ImportError, RuntimeError):
    NAU7802_AVAILABLE = False


class NAU7802Scale(ScaleInterface):
    """Scale using NAU7802 I2C load cell amplifier."""

    def __init__(self, config: NAU7802ScaleConfig, hardware: HardwareContext) -> None:
        if not NAU7802_AVAILABLE:
            msg = "cedargrove_nau7802 library is not available. Cannot initialize NAU7802 scale."
            _logger.error(msg)
            raise ImportError(msg)
        super().__init__(config, hardware)
        self._zero_offset: int = 0
        i2c = get_i2c()
        if i2c is None:
            msg = "I2C bus is not available. Cannot initialize NAU7802 scale."
            _logger.error(msg)
            raise RuntimeError(msg)
        self._nau = NAU7802(i2c, address=config.address_hex)
        # PGA gain: amplifies the load cell signal (1-128); 128 is typical for low mV/V load cells
        self._nau.gain = 128
        # ADC sample rate in SPS (10/20/40/80/320); 80 SPS = ~12.5ms per reading
        self._nau.conversion_rate = 80
        self._nau.channel = 1
        _logger.log_event("INFO", f"NAU7802 scale initialized (address=0x{config.i2c_address})")

    def _sample_raw(self, samples: int) -> int:
        readings = [self._nau.read() for _ in range(max(1, samples))]
        return int(sum(readings) / len(readings))

    def tare(self, samples: int = 3) -> int:
        self._zero_offset = self._sample_raw(samples)
        return self._zero_offset

    def read_grams(self) -> float:
        return (self._sample_raw(1) - self._zero_offset) / self._calibration_factor

    def read_raw(self, samples: int = 1) -> int:
        return self._sample_raw(samples)

    def get_gross_grams(self) -> float:
        """Return the absolute weight in grams relative to the empty scale calibration."""
        return (self._sample_raw(1) - self._zero_raw_offset) / self._calibration_factor

    def cleanup(self) -> None:
        self._nau.enable = False
