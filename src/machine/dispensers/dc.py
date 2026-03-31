from __future__ import annotations

import time

from src.config.config_types import PinId
from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser, ProgressCallback
from src.machine.pin_controller import PinController

_logger = LoggerHandler("DCDispenser")

_LOOP_INTERVAL = 0.01
"""Sleep interval in seconds for the dispense loop (~100Hz)."""


class DCDispenser(BaseDispenser):
    """Dispenser for DC pumps controlled via relay pins.

    Uses time-based dispensing: activates a pin for a calculated duration
    based on amount and flow rate, then deactivates it.
    """

    def __init__(self, slot: int, volume_flow: float, pin_id: PinId, pin_controller: PinController) -> None:
        super().__init__(slot, volume_flow)
        self.pin_id = pin_id
        self._pin_controller = pin_controller

    def setup(self) -> None:
        self._pin_controller.initialize_pin(self.pin_id)

    def dispense(self, amount_ml: float, pump_speed: int, callback: ProgressCallback) -> float:
        self._stop_event.clear()
        flow_rate = self.volume_flow * pump_speed / 100
        flow_time = amount_ml / flow_rate
        _logger.info(f"<o> Slot {self.slot:<2} {self.pin_id!s:<14}| dispensing {amount_ml:.0f}ml over {flow_time:.1f}s")
        self._pin_controller.activate_pin(self.pin_id)
        start = time.perf_counter()
        consumption = 0.0
        try:
            while not self._stop_event.is_set():
                elapsed = time.perf_counter() - start
                if elapsed >= flow_time:
                    consumption = flow_rate * flow_time
                    break
                consumption = flow_rate * elapsed
                callback(consumption, False)
                time.sleep(_LOOP_INTERVAL)
        finally:
            self._pin_controller.close_pin(self.pin_id)
        _logger.info(f"<x> Slot {self.slot:<2} {self.pin_id!s:<14}| dispensed {consumption:.0f}ml")
        callback(consumption, True)
        return consumption

    def stop(self) -> None:
        self._stop_event.set()
        self._pin_controller.close_pin(self.pin_id)

    def cleanup(self) -> None:
        self.stop()
