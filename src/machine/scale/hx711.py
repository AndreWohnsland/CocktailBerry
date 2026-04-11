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
        self._data_pin = config.data_pin
        self._clock_pin = config.clock_pin
        self._calibration_factor = config.calibration_factor
        self._offset = 0
        self._dt = DigitalInputDevice(self._data_pin, pull_up=False)
        self._sck = DigitalOutputDevice(self._clock_pin, active_high=True, initial_value=False)
        _logger.log_event("INFO", f"HX711 scale initialized (data={self._data_pin}, clock={self._clock_pin})")

    def _read_raw(self, timeout: float = 0.5) -> int:
        """Read a single 24-bit raw value from HX711."""
        t_end = time.time() + timeout
        while self._dt.value == 1:
            if time.time() > t_end:
                _logger.log_event("WARNING", "HX711: Timeout waiting for data ready")
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

    def tare(self, samples: int = 10) -> None:
        """Set offset to current (empty) value."""
        readings = [self._read_raw() for _ in range(max(1, samples))]
        self._offset = int(sum(readings) / len(readings))
        _logger.log_event("INFO", f"HX711 tare set, new offset: {self._offset}")

    def read_grams(self, samples: int = 5) -> float:
        """Return average weight in grams."""
        readings = [self._read_raw() for _ in range(max(1, samples))]
        avg = sum(readings) / len(readings)
        return (avg - self._offset) / self._calibration_factor if self._calibration_factor else 0.0

    def read_raw(self, samples: int = 5) -> float:
        """Return average raw value (offset subtracted)."""
        readings = [self._read_raw() for _ in range(max(1, samples))]
        avg = sum(readings) / len(readings)
        return avg - self._offset

    def calibrate_with_known_weight(self, weight_g: float, samples: int = 10) -> float:
        """Calibrate scale factor using a known weight (after tare)."""
        if weight_g <= 0:
            _logger.log_event("ERROR", "Calibration weight must be > 0")
            return self._calibration_factor
        readings = [self._read_raw() for _ in range(max(1, samples))]
        avg = sum(readings) / len(readings)
        if avg == self._offset:
            _logger.log_event("ERROR", "Calibration: raw == offset, no measurable difference")
            return self._calibration_factor
        self._calibration_factor = (avg - self._offset) / float(weight_g)
        _logger.log_event(
            "INFO",
            f"HX711 calibrated: avg={avg:.1f}, offset={self._offset}, scale_factor={self._calibration_factor:.5f}",
        )
        return self._calibration_factor

    def get_calibration(self) -> tuple[float, int]:
        return self._calibration_factor, self._offset

    def set_calibration(self, scale_factor: float, offset: int) -> None:
        self._calibration_factor = float(scale_factor) if scale_factor else 1.0
        self._offset = int(offset)
        _logger.log_event(
            "INFO", f"HX711 calibration set: scale_factor={self._calibration_factor}, offset={self._offset}"
        )

    def cleanup(self) -> None:
        self._sck.close()
        self._dt.close()
        _logger.log_event("INFO", "HX711 cleaned up")
