from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.leds.base import LedInterface

if TYPE_CHECKING:
    from src.config.config_types import NormalLedConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("NormalLed")


class NormalLed(LedInterface):
    """Plain on/off LED driven by a single GPIO/expander pin."""

    def __init__(self, config: NormalLedConfig, hardware: HardwareContext) -> None:
        super().__init__(config, hardware)
        self.pin_id = config.pin_id
        self._pin_controller = hardware.pin_controller
        _logger.info(f"<i> Initializing normal LED on pin {self.pin_id}")
        self._pin_controller.initialize_pin(self.pin_id)

    def turn_on(self) -> None:
        self._pin_controller.activate_pin(self.pin_id)

    def turn_off(self) -> None:
        self._pin_controller.close_pin(self.pin_id)

    def end_frames(self) -> Iterator[float]:
        """Blink at 5 Hz for 5 seconds."""
        step = 0.1
        duration = 5.0
        elapsed = 0.0
        while elapsed < duration:
            self.turn_on()
            yield step
            elapsed += step
            self.turn_off()
            yield step
            elapsed += step
