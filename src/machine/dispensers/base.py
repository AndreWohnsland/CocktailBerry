from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from threading import Event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config_types import BasePumpConfig
    from src.machine.hardware import HardwareContext

ProgressCallback = Callable[[float, bool], None]
"""Callback signature: (consumption_ml, is_done) -> None"""


class BaseDispenser(ABC):
    """Base class for all dispenser types.

    Each dispenser controls one pump slot. Subclasses implement
    ``_dispense_steps()`` as a generator that yields consumption values.
    The concrete ``dispense()`` method handles stop-event management,
    scale taring, and progress callbacks automatically.
    """

    def __init__(
        self,
        slot: int,
        config: BasePumpConfig,
        hardware: HardwareContext,
    ) -> None:
        self.slot = slot
        self.config = config
        self.volume_flow = config.volume_flow
        self._stop_event = Event()
        self.hardware = hardware
        self._scale = hardware.scale if config.consumption_estimation == "weight" else None
        self.carriage_position = config.carriage_position

    @property
    def needs_exclusive(self) -> bool:
        """True when this dispenser requires exclusive scheduling (i.e. it uses a scale)."""
        return self._scale is not None

    def dispense(self, amount_ml: float, pump_speed: int, callback: ProgressCallback) -> float:
        """Dispense the given amount at the given pump speed.

        This is a template method that drives ``_dispense_steps()``.
        It handles clearing/checking the stop event, taring the scale,
        and calling the progress callback. Subclasses normally only need
        to implement ``_dispense_steps()``.

        pump_speed is the percentage of the pump's configured volume_flow
        (100 = full speed). Returns actual consumption in ml.
        """
        self._stop_event.clear()
        if self._scale is not None:
            self._scale.tare()
        consumption = 0.0
        callback(consumption, False)
        for consumption in self._dispense_steps(amount_ml, pump_speed):
            if self._stop_event.is_set():
                break
            callback(consumption, False)
        callback(consumption, True)
        return consumption

    @abstractmethod
    def _dispense_steps(self, amount_ml: float, pump_speed: int) -> Generator[float]:
        """Yield consumption values during dispensing.

        The base ``dispense()`` iterates this generator and handles:
        - Clearing / checking the stop event (cancellation)
        - Taring the scale (if present)
        - Calling progress callbacks

        Implementations should:
        1. Activate hardware, then yield consumption updates in a loop.
        2. Use ``self._get_consumption(estimate)`` to read the scale when
           available or fall back to a time/step-based estimate.
        3. Use ``try/finally`` for hardware cleanup — the generator is
           automatically closed on cancellation, so ``finally`` runs
           in both normal and stop scenarios.

        Minimal example::

            def _dispense_steps(self, amount_ml, pump_speed):
                flow = self.volume_flow * pump_speed / 100
                elapsed = 0.0
                try:
                    self._activate()
                    while True:
                        time.sleep(0.01)
                        elapsed += 0.01
                        consumption = self._get_consumption(elapsed * flow)
                        yield consumption
                        if consumption >= amount_ml:
                            return
                finally:
                    self._deactivate()
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
