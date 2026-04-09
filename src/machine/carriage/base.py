from __future__ import annotations

from abc import ABC, abstractmethod

from src.config.config_types import BaseCarriageConfig


class CarriageInterface(ABC):
    """Abstract interface for a linear carriage/slide used for positioning.

    A carriage moves a glass (or similar) along a rail to position it under
    the correct dispenser. Positions are abstract values from 0 to 100
    representing the percentage of the total travel range.
    Implementation must track the current position internally,
    and initialize() should set this tracking attribute.
    """

    def __init__(self, config: BaseCarriageConfig) -> None:
        self.config = config
        self.home_position = config.home_position
        self.speed_pct_per_s = config.speed_pct_per_s
        self.move_during_cleaning = config.move_during_cleaning
        self.wait_after_dispense = config.wait_after_dispense

    @abstractmethod
    def initialize(self) -> None:
        """Drive to the reference sensor and establish the current position.

        Must be called once at program start. The carriage may be at any
        unknown position initially. This method drives toward a reference
        sensor (e.g. an end stop), and once the sensor is triggered the
        internal position is set to the known reference value (typically 0/100).
        After this method returns, the carriage position is known and
        ``move_to`` / ``home`` can be used reliably.
        """

    @abstractmethod
    def move_to(self, position: int) -> None:
        """Move the carriage to the given position (0-100) in percentage."""

    @abstractmethod
    def home(self) -> None:
        """Return the carriage to its configured home position (self.home_position)."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware resources."""

    def travel_time(self, from_pos: int, to_pos: int) -> float:
        """Estimate the travel time in seconds between two positions.

        Uses speed_pct_per_s from config: time = |delta| / speed.
        """
        if self.speed_pct_per_s <= 0:
            return 0.0
        return abs(to_pos - from_pos) / self.speed_pct_per_s
