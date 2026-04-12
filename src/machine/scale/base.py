from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config_types import BaseScaleConfig


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
    def tare(self) -> None:
        """Capture the current raw reading as the dynamic tare offset.

        All subsequent read_grams() and read_raw() calls are relative to this point.
        Does not affect zero_raw_offset or get_gross_grams().
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
