from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.config.config_types import BaseCarriageConfig

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext


class CarriageInterface(ABC):
    """Abstract interface for a linear carriage/slide used for positioning.

    A carriage moves a glass (or similar) along a rail to position it under
    the correct dispenser. Positions are abstract values from 0 to 100
    representing the percentage of the total travel range; the extension is
    responsible for mapping that axis onto its native unit (e.g. motor steps).
    Implementation must track the current position internally,
    and find_reference() should set this tracking attribute.

    The ``hardware`` argument gives access to the full HardwareContext (pin
    controller, LEDs, scale, and the ``extra`` dict of hardware extension
    instances). Built-in/stub implementations may ignore it; custom carriage
    extensions can use it to reach shared hardware (e.g. a UART controller).
    """

    def __init__(self, config: BaseCarriageConfig, hardware: HardwareContext) -> None:
        self.config = config
        self.hardware = hardware
        self.home_position = config.home_position
        self.speed_pct_per_s = config.speed_pct_per_s
        self.move_during_cleaning = config.move_during_cleaning
        self.wait_after_dispense = config.wait_after_dispense

    @abstractmethod
    def find_reference(self) -> None:
        """Drive to the reference sensor and establish the current position.

        Called once after the GUI/API is up (from
        :meth:`MachineController.find_carriage_reference`). May be invoked
        again at runtime (for example after a mechanical intervention or via
        a maintenance action), so implementations must remain idempotent and
        leave the carriage at a known position on return.

        The carriage may be at any unknown position initially. This method
        drives toward a reference sensor (e.g. an end stop), and once the
        sensor is triggered the internal position is set to the known
        reference value (typically 0 or 100). After this method returns,
        the carriage position is known and ``move_to`` / ``home`` can be
        used reliably.
        """

    @abstractmethod
    def move_to(self, position: int) -> None:
        """Move the carriage to the given position (0-100) in percentage.

        The 0-100 axis is abstract: implementations map it to their native
        unit (motor steps, encoder ticks, servo angle, …).
        """

    @abstractmethod
    def home(self) -> None:
        """Return the carriage to its configured home position (self.home_position)."""

    @abstractmethod
    def jog(self, delta: int) -> None:
        """Move the carriage by a small signed delta without re-homing.

        ``delta`` is expressed in the implementation's native smallest-move
        unit — typically one motor step for stepper-based carriages, or
        one position unit (1% of travel) for percent-only carriages. A
        positive value moves the carriage away from home, a negative value
        toward home (consistency with ``move_to``).

        Intended for commissioning and maintenance flows (e.g. teaching slot
        positions). Implementations should keep each call bounded and safe
        to issue repeatedly; bulk motion belongs in ``move_to``.
        """

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
