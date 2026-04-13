from __future__ import annotations

import time
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface

if TYPE_CHECKING:
    from src.config.config_types import HX711ScaleConfig

try:
    from gpiozero import DigitalInputDevice, DigitalOutputDevice

    GPIOZERO_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    GPIOZERO_AVAILABLE = False

_logger = LoggerHandler("HX711Scale")


class HX711Scale(ScaleInterface):
    """Robust HX711 scale using gpiozero, Pi 5 compatible."""

    def __init__(self, config: HX711ScaleConfig) -> None:
        if not GPIOZERO_AVAILABLE:
            msg = "gpiozero library is not available. Cannot initialize HX711 scale."
            _logger.log_event("ERROR", msg)
            raise ImportError(msg)
        super().__init__(config)
        self._data_pin = config.data_pin
        self._clock_pin = config.clock_pin
        self._offset = 0
        self._dt = DigitalInputDevice(self._data_pin, pull_up=False)
        self._sck = DigitalOutputDevice(self._clock_pin, active_high=True, initial_value=False)
        _logger.info(f"HX711 scale initialized (data={self._data_pin}, clock={self._clock_pin})")

    def _read_raw_over_sck(self, timeout: float = 0.5) -> int:
        """Read a single 24-bit raw value from HX711.

        One call = one complete ADC conversion: wait for the chip to signal
        data ready, then clock out all 24 bits via bit-bang. Duration is
        determined by the chip's sample rate (~100ms at 10 SPS, ~12.5ms at 80 SPS).

        The sample rate is hardware-only — set by the RATE pin on the HX711 chip:
        RATE tied to GND = 10 SPS (default), RATE tied to VCC = 80 SPS.
        Many breakout boards expose this as a solder bridge labeled "80Hz".
        There is no software way to change it.
        """
        t_end = time.time() + timeout
        while self._dt.value == 1:
            if time.time() > t_end:
                _logger.warning("HX711: Timeout waiting for data ready")
                return 0
            time.sleep(0.001)
        value = 0
        for _ in range(24):
            self._sck.on()
            value = (value << 1) | (1 if self._dt.value else 0)
            self._sck.off()
        # Gain setting: 1 extra clock (128x gain, channel A)
        self._sck.on()
        self._sck.off()
        # Two's complement
        if value & 0x800000:
            value -= 1 << 24
        return value

    def _sample_raw_over_sck(self, samples: int) -> int:
        """Read raw value n times and return the average."""
        readings = [self._read_raw_over_sck() for _ in range(max(1, samples))]
        return int(sum(readings) / len(readings))

    def tare(self, samples: int = 3) -> float:
        """Set offset to current (empty) value."""
        self._offset = self._sample_raw_over_sck(samples)
        _logger.debug(f"HX711 tare set, new offset: {self._offset}")
        return float(self._offset)

    def read_grams(self) -> float:
        """Return average weight in grams."""
        return self.read_raw(samples=1) / self._calibration_factor

    def read_raw(self, samples: int = 1) -> float:
        """Return average raw value (offset subtracted)."""
        return self._sample_raw_over_sck(samples) - self._offset

    def get_gross_grams(self) -> float:
        """Return the absolute weight in grams relative to the empty scale calibration."""
        return (self._sample_raw_over_sck(1) - self._zero_raw_offset) / self._calibration_factor

    def cleanup(self) -> None:
        self._sck.close()
        self._dt.close()
        _logger.info("HX711 cleaned up")
