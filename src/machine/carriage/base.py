from __future__ import annotations

from abc import ABC, abstractmethod

from src.config.config_manager import CONFIG as cfg


class CarriageInterface(ABC):
    """Abstract interface for a linear carriage/slide used for positioning.

    A carriage moves a glass (or similar) along a rail to position it under
    the correct dispenser. Positions are abstract values from 0 to 100
    representing the percentage of the total travel range.
    """

    @abstractmethod
    def move_to(self, position: int) -> None:
        """Move the carriage to the given position (0-100)."""

    @abstractmethod
    def home(self) -> None:
        """Return the carriage to its configured home position."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware resources."""

    def travel_time(self, from_pos: int, to_pos: int) -> float:
        """Estimate the travel time in seconds between two positions.

        Uses speed_pct_per_s from config: time = |delta| / speed.
        """
        speed = cfg.CARRIAGE_CONFIG.speed_pct_per_s
        if speed <= 0:
            return 0.0
        return abs(to_pos - from_pos) / speed
