from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler

if TYPE_CHECKING:
    from src.config.config_types import BaseScaleConfig


_logger = LoggerHandler("BaseScale")


class ScaleInterface(ABC):
    """Abstract interface for a weight scale used in weight-based dispensing.

    A single scale instance is shared across all dispensers via HardwareContext.
    Because only one dispenser can use the scale at a time, any dispenser that
    has a scale reference automatically requires exclusive scheduling.
    """

    def __init__(self, config: BaseScaleConfig) -> None:
        self._calibration_factor = config.calibration_factor
        self._zero_raw_offset = config.zero_raw_offset

    @abstractmethod
    def tare(self, samples: int = 3) -> float:
        """Capture the current raw reading as the dynamic tare offset.

        All subsequent read_grams() and read_raw() calls are relative to this point.
        Does not affect zero_raw_offset or get_gross_grams().
        Returns the raw offset value that was captured.
        """

    @abstractmethod
    def read_grams(self) -> float:
        """Return the weight in grams relative to the last tare() call."""

    @abstractmethod
    def read_raw(self, samples: int = 1) -> float:
        """Return the average raw ADC reading relative to the last tare() call (before calibration factor).

        samples: number of readings to average, higher values reduce noise but increase latency
        (each ADC reading is rate-limited by the hardware, typically 10-80 SPS).
        Used during calibration to compute the calibration factor:
        calibration_factor = read_raw() / known_weight_grams
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware resources held by the scale."""

    @abstractmethod
    def get_gross_grams(self) -> float:
        """Return the absolute weight in grams relative to the initial empty scale.

        Uses _zero_raw_offset (the raw ADC reading of the empty scale recorded during
        one-time calibration), not the dynamic tare offset set by tare(). This allows
        detecting whether anything is on the scale regardless of prior tare calls.
        """

    def calibrate_with_known_weight(self, weight_g: float, samples: int = 10) -> float:
        """Calibrate scale factor using a known weight (after tare).

        Overwrite this if your scale requires a different calibration procedure.
        """
        if weight_g <= 0:
            _logger.error("Calibration weight must be > 0")
            return self._calibration_factor
        factor = self.read_raw(samples) / weight_g
        self.set_calibration_factor(factor)
        return self._calibration_factor

    def set_calibration_factor(self, calibration_factor: float) -> None:
        """Set the calibration factor directly (bypassing tare and calibrate_with_known_weight).

        Overwrite this if you need other specific logic.
        """
        self._calibration_factor = calibration_factor
        _logger.info(f"Scale calibration factor set: scale_factor={self._calibration_factor}")

    def set_zero_raw_offset(self, zero_raw_offset: float) -> None:
        """Set the zero raw offset directly (bypassing tare).

        Overwrite this if you need other specific logic.
        """
        self._zero_raw_offset = zero_raw_offset
        _logger.info(f"Scale zero raw offset set: zero_raw_offset={self._zero_raw_offset}")
