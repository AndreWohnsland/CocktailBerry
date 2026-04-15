from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.scale.base import ScaleInterface

if TYPE_CHECKING:
    from src.config.config_types import HX711ScaleConfig
    from src.machine.hardware import HardwareContext

try:
    from HX711 import Mass, Options, ReadType, SimpleHX711

    HX711_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    HX711_AVAILABLE = False

_logger = LoggerHandler("HX711Scale")

# LIBRARY INFORMATION
# read() will always return raw (without offset)
# zero() will set the library's internal offset
# getOffset() returns the library's internal offset
# weight() returns (raw - library_offset) / calibration_factor


class HX711Scale(ScaleInterface):
    """HX711 scale using hx711-rpi-py backend."""

    def __init__(self, config: HX711ScaleConfig, hardware: HardwareContext) -> None:
        if not HX711_AVAILABLE:
            msg = "hx711-rpi-py library is not available."
            _logger.log_event("ERROR", msg)
            raise ImportError(msg)

        super().__init__(config, hardware)
        self._zero_raw_offset = config.zero_raw_offset

        self._hx = SimpleHX711(
            config.data_pin,
            config.clock_pin,
            int(config.calibration_factor),
            int(config.zero_raw_offset),
        )
        self._hx.setUnit(Mass.Unit.G)

        _logger.info(f"HX711 scale initialized via hx711-rpi-py (data={config.data_pin}, clock={config.clock_pin})")

    def tare(self, samples: int = 3) -> int:
        """Set offset to current (empty) value."""
        self._hx.zero(Options(samples, ReadType.Median))
        offset = int(self._hx.getOffset())
        _logger.debug(f"HX711 tare set, new offset: {offset}")
        return offset

    def read_raw(self, samples: int = 1) -> int:
        """Return raw ADC reading relative to the last tare() call (before calibration factor)."""
        return self._hx.read(Options(samples, ReadType.Median))

    def read_grams(self) -> float:
        """Return weight in grams relative to the last tare() call."""
        # This will return a Mass class, we need to get this value
        return round(self._hx.weight(1).getValue(), 2)

    def get_gross_grams(self) -> float:
        """Return absolute weight using the initial zero calibration offset."""
        raw = int(self._hx.read())
        return (raw - self._zero_raw_offset) / self._calibration_factor

    def cleanup(self) -> None:
        with contextlib.suppress(Exception):
            self._hx.disconnect()
        _logger.info("HX711 cleaned up")

    def set_calibration_factor(self, calibration_factor: float) -> None:
        self._hx.setReferenceUnit(int(calibration_factor))
        self._calibration_factor = calibration_factor
        _logger.info(f"Scale calibration factor set: scale_factor={self._calibration_factor}")

    def set_zero_raw_offset(self, zero_raw_offset: float) -> None:
        # Only update the Python-side value used by get_gross_grams().
        # The library's internal offset is managed exclusively by zero() (tare).
        self._zero_raw_offset = zero_raw_offset
        _logger.info(f"Scale zero raw offset set: zero_raw_offset={self._zero_raw_offset}")
