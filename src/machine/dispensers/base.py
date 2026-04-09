from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from threading import Event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config_types import BasePumpConfig
    from src.machine.scale import ScaleInterface

ProgressCallback = Callable[[float, bool], None]
"""Callback signature: (consumption_ml, is_done) -> None"""


class BaseDispenser(ABC):
    """Base class for all dispenser types.

    Each dispenser controls one pump slot. The dispense() method is blocking
    and should be called from a worker thread by the MachineController.
    """

    def __init__(self, slot: int, config: BasePumpConfig, scale: ScaleInterface | None = None) -> None:
        self.slot = slot
        self.config = config
        self.volume_flow = config.volume_flow
        self._stop_event = Event()
        self._scale = scale
        self.carriage_position = config.carriage_position

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

        Important: call self._stop_event.clear() at the start of your implementation
        to reset the event from any previous stop() call.
        """

    def stop(self) -> None:
        """Emergency stop / cancel current dispensing.

        Sets the stop event so the dispense loop exits.
        Override this if you need additional hardware cleanup on stop
        (e.g. closing a relay pin), but always call super().stop().
        """
        self._stop_event.set()

    def cleanup(self) -> None:
        """Release hardware resources.

        Called at program shutdown. Override if your dispenser holds
        hardware resources that need explicit release.
        The default implementation does nothing.
        """

    def _get_consumption(self, current_estimate: float) -> float:
        """Return current consumption in ml.

        When a scale is present, reads grams directly (density assumed ~1 g/ml).
        Otherwise returns the caller's time/step-based estimate.
        """
        if self._scale is not None:
            return self._scale.read_grams()
        return current_estimate
