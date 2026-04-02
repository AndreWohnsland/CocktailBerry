from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from threading import Event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.machine.scale import ScaleInterface

ProgressCallback = Callable[[float, bool], None]
"""Callback signature: (consumption_ml, is_done) -> None"""


class BaseDispenser(ABC):
    """Base class for all dispenser types.

    Each dispenser controls one pump slot. The dispense() method is blocking
    and should be called from a worker thread by the MachineController.
    """

    def __init__(self, slot: int, volume_flow: float, scale: ScaleInterface | None = None) -> None:
        self.slot = slot
        self.volume_flow = volume_flow
        self._stop_event = Event()
        self._scale = scale

    @property
    def needs_exclusive(self) -> bool:
        """True when this dispenser requires exclusive scheduling (i.e. it uses a scale)."""
        return self._scale is not None

    @abstractmethod
    def setup(self) -> None:
        """Initialize hardware resources for this dispenser."""

    @abstractmethod
    def dispense(self, amount_ml: float, pump_speed: int, callback: ProgressCallback) -> float:
        """Dispense the given amount at the given pump speed.

        This method is blocking and returns the actual consumption in ml.
        The callback is called periodically with (consumption_ml, is_done).
        Implementations should check self._stop_event to support cancellation.
        pump_speed is the percentage of the pump's configured volume_flow (100 = full speed).
        """

    @abstractmethod
    def stop(self) -> None:
        """Emergency stop / cancel current dispensing."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release hardware resources."""

    def estimated_time(self, amount_ml: float, pump_speed: int) -> float:
        """Calculate estimated dispense time in seconds. Used for scheduling."""
        return amount_ml / (self.volume_flow * pump_speed / 100)

    def _get_consumption(self, current_estimate: float) -> float:
        """Return current consumption in ml.

        When a scale is present, reads grams directly (density assumed ~1 g/ml).
        Otherwise returns the caller's time/step-based estimate.
        """
        if self._scale is not None:
            return self._scale.read_grams()
        return current_estimate
