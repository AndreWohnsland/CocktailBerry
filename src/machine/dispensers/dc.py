from __future__ import annotations

import time
from collections.abc import Generator
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser

if TYPE_CHECKING:
    from src.config.config_types import DCPumpConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("DCDispenser")

_LOOP_INTERVAL = 0.01
"""Sleep interval in seconds for the dispense loop (~100Hz)."""


class DCDispenser(BaseDispenser):
    """Dispenser for DC pumps controlled via relay pins.

    Uses time-based dispensing by default: activates a pin for a calculated
    duration based on amount and flow rate. When a scale is provided, dispensing
    stops as soon as the measured weight reaches the target amount instead.
    """

    def __init__(
        self,
        slot: int,
        config: DCPumpConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(slot, config, hardware)
        self.pin_id = config.pin_id
        self._pin_controller = hardware.pin_controller

    def setup(self) -> None:
        self._pin_controller.initialize_pin(self.pin_id)

    def _dispense_steps(self, amount_ml: float, pump_speed: int) -> Generator[float]:
        flow_rate = self.volume_flow * pump_speed / 100
        flow_time = amount_ml / flow_rate
        mode = "scale" if self._scale is not None else f"{flow_time:.1f}s"
        _logger.info(f"<o> Slot {self.slot:<2} {self.pin_id!s:<14}| dispensing {amount_ml:.0f}ml ({mode})")
        self._pin_controller.activate_pin(self.pin_id)
        start = time.perf_counter()
        consumption = 0.0
        try:
            while True:
                elapsed = time.perf_counter() - start
                consumption = self._get_consumption(flow_rate * elapsed)
                yield consumption
                if consumption >= amount_ml:
                    return
                time.sleep(_LOOP_INTERVAL)
        finally:
            self._pin_controller.close_pin(self.pin_id)
            _logger.info(f"<x> Slot {self.slot:<2} {self.pin_id!s:<14}| dispensed {consumption:.0f}ml")

    def stop(self) -> None:
        super().stop()
        self._pin_controller.close_pin(self.pin_id)

    def cleanup(self) -> None:
        self.stop()
        self._pin_controller.cleanup_pin(self.pin_id)
