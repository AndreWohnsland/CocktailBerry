from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.machine.carriage import CarriageInterface
from src.machine.leds import LedController
from src.machine.pin_controller import PinController
from src.machine.scale import ScaleInterface


@dataclass
class HardwareContext:
    """Shared hardware resources passed to dispensers and other components.

    Centralizes access to hardware controllers so that new components
    (e.g. scale, carriage) can be added without changing every call signature.
    """

    pin_controller: PinController
    led_controller: LedController
    scale: ScaleInterface | None = field(default=None)
    carriage: CarriageInterface | None = field(default=None)
    extra: dict[str, Any] = field(default_factory=dict)

    def cleanup(self) -> None:
        """Shut down all hardware: turn off LEDs and release all pins."""
        self.led_controller.turn_off()
        self.pin_controller.cleanup_pin_list()
        if self.scale is not None:
            self.scale.cleanup()
        if self.carriage is not None:
            self.carriage.cleanup()
