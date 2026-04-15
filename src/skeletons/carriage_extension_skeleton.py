from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_types import BaseCarriageConfig, ConfigInterface, IntType
from src.config.validators import build_number_limiter
from src.logger_handler import LoggerHandler
from src.machine.carriage.base import CarriageInterface

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is a carriage extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/#carriages
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name shown in the carriage type dropdown
#   CONFIG_FIELDS  - dict of extra config fields (beyond the shared BaseCarriageConfig fields)
#   ExtensionConfig - config class inheriting from BaseCarriageConfig
#   Implementation - carriage class inheriting from CarriageInterface
#
# Shared fields (carriage_type, enabled, home_position, speed_pct_per_s,
# move_during_cleaning, wait_after_dispense) are auto-injected — only define
# your EXTRA fields in CONFIG_FIELDS.


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ExtensionConfig(BaseCarriageConfig):
    """Custom configuration for this carriage type.

    Add any extra attributes your carriage needs beyond the shared ones.
    """

    step_pin: int
    dir_pin: int

    def __init__(
        self,
        step_pin: int = 0,
        dir_pin: int = 0,
        carriage_type: str = EXTENSION_NAME,
        enabled: bool = False,
        home_position: int = 0,
        speed_pct_per_s: float = 10.0,
        move_during_cleaning: bool = False,
        wait_after_dispense: float = 0.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            carriage_type=carriage_type,
            enabled=enabled,
            home_position=home_position,
            speed_pct_per_s=speed_pct_per_s,
            move_during_cleaning=move_during_cleaning,
            wait_after_dispense=wait_after_dispense,
        )
        self.step_pin = step_pin
        self.dir_pin = dir_pin

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update({"step_pin": self.step_pin, "dir_pin": self.dir_pin})
        return config


# Only define the EXTRA fields here. Shared fields (enabled, home_position,
# speed_pct_per_s, move_during_cleaning, wait_after_dispense) and the
# carriage_type dropdown are auto-injected by the extension manager.
CONFIG_FIELDS: dict[str, ConfigInterface] = {
    "step_pin": IntType([build_number_limiter(0)], prefix="Step:"),
    "dir_pin": IntType([build_number_limiter(0)], prefix="Dir:"),
}


class Implementation(CarriageInterface):
    """Custom carriage implementation.

    Implement the abstract methods of CarriageInterface to drive your hardware.

    Inherited attributes from CarriageInterface:
      self.config               — your ExtensionConfig instance
      self.hardware            — HardwareContext with pin_controller, led_controller,
                                 scale, and extra (dict of hardware extension instances)
      self.home_position       — home position (0-100), from config
      self.speed_pct_per_s     — movement speed in % of travel per second, from config
      self.move_during_cleaning — whether the carriage should move during cleaning
      self.wait_after_dispense — pause in seconds after each dispense before moving

    Abstract methods you MUST implement:
      find_reference()         — drive to reference sensor; set internal position
      move_to(position)        — move to position (0-100)
      home()                   — return to self.home_position
      jog(delta)               — move by signed delta in native smallest-move unit
                                 (typically one motor step)
      cleanup()                — release hardware resources

    Base class helpers you may use or override:
      travel_time(from_pos, to_pos) — default seconds estimate from speed_pct_per_s
    """

    def __init__(
        self,
        config: ExtensionConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self._step_pin = config.step_pin
        self._dir_pin = config.dir_pin
        # Track the current position in percent (0-100). Must be set in find_reference().
        self._position = 0
        # >>> Initialize your hardware here (e.g. configure GPIO for step/dir pins) <<<
        _logger.info(f"Carriage '{EXTENSION_NAME}' initialized (step={self._step_pin}, dir={self._dir_pin})")

    def find_reference(self) -> None:
        """Drive to the reference sensor and establish the current position.

        Called once after the GUI/API is up. May be invoked again at
        runtime; must remain idempotent and leave the carriage at a known
        position on return.
        """
        # >>> Drive toward the endstop until triggered, then set position <<<
        _logger.info(f"Carriage '{EXTENSION_NAME}': driving to reference sensor")
        self._position = 0

    def move_to(self, position: int) -> None:
        """Move the carriage to the given position (0-100)."""
        target = max(0, min(100, position))
        if target == self._position:
            return
        # >>> Translate percent delta to motor steps and drive the motor <<<
        _logger.debug(f"Carriage '{EXTENSION_NAME}': moving from {self._position} to {target}")
        self._position = target

    def home(self) -> None:
        """Return the carriage to its configured home position."""
        self.move_to(self.home_position)

    def jog(self, delta: int) -> None:
        """Move by a small signed delta in the implementation's native smallest unit.

        For a stepper-based carriage this is typically one motor step. The
        translation to the abstract 0-100 axis is up to the implementation.
        """
        # >>> Pulse the step pin ``abs(delta)`` times in the direction of sign <<<
        _logger.debug(f"Carriage '{EXTENSION_NAME}': jog {delta} step(s)")

    def cleanup(self) -> None:
        """Release hardware resources."""
        # >>> Close your hardware here (e.g. release GPIO pins) <<<
        _logger.info(f"Carriage '{EXTENSION_NAME}' cleaned up")
