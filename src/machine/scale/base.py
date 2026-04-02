from __future__ import annotations

from abc import ABC, abstractmethod


class ScaleInterface(ABC):
    """Abstract interface for a weight scale used in weight-based dispensing.

    A single scale instance is shared across all dispensers via HardwareContext.
    Because only one dispenser can use the scale at a time, any dispenser that
    has a scale reference automatically requires exclusive scheduling.
    """

    @abstractmethod
    def tare(self) -> None:
        """Zero the scale (set current reading as the baseline)."""

    @abstractmethod
    def read_grams(self) -> float:
        """Return the current weight reading in grams since last tare."""

    @abstractmethod
    def read_raw(self) -> float:
        """Return the raw ADC reading (after tare offset, before calibration factor).

        Used during calibration to compute the calibration factor:
        calibration_factor = read_raw() / known_weight_grams
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware resources held by the scale."""
