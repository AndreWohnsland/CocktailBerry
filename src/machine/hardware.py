from __future__ import annotations

from dataclasses import dataclass

from src.machine.leds import LedController
from src.machine.pin_controller import PinController


@dataclass
class HardwareContext:
    """Shared hardware resources passed to dispensers and other components.

    Centralizes access to hardware controllers so that new components
    (e.g. scale, carriage) can be added without changing every call signature.
    """

    pin_controller: PinController
    led_controller: LedController

    def cleanup(self) -> None:
        """Shut down all hardware: turn off LEDs and release all pins."""
        self.led_controller.turn_off()
        self.pin_controller.cleanup_pin_list()
