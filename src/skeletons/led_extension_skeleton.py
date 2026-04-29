from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from src import SupportedLedStatesType
from src.config.config_types import BaseLedConfig, ConfigInterface, StringType
from src.logger_handler import LoggerHandler
from src.machine.leds.base import LedInterface

if TYPE_CHECKING:
    from src.machine.hardware import HardwareContext

# Auto created by CocktailBerry CLI version VERSION_HOLDER
# This is an LED extension skeleton.
# For more information see: https://docs.cocktailberry.org/hardware-extensions/#leds
# Your custom extension needs four exports:
#   EXTENSION_NAME - unique name shown in the led type dropdown
#   CONFIG_FIELDS  - dict of extra config fields (beyond the shared BaseLedConfig fields)
#   ExtensionConfig - config class inheriting from BaseLedConfig
#   Implementation - led class inheriting from LedInterface
#
# Shared fields (led_type, default_on, preparation_state) are auto-injected —
# only define your EXTRA fields in CONFIG_FIELDS.


EXTENSION_NAME = "EXTENSION_NAME_HOLDER"
_logger = LoggerHandler("EXTENSION_NAME_HOLDER")


class ExtensionConfig(BaseLedConfig):
    """Custom configuration for this LED type.

    Add any extra attributes your LED needs beyond the shared ones.
    """

    label: str

    def __init__(
        self,
        label: str = "default",
        led_type: str = EXTENSION_NAME,
        default_on: bool = False,
        preparation_state: SupportedLedStatesType = "Effect",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            led_type=led_type,
            default_on=default_on,
            preparation_state=preparation_state,
        )
        self.label = label

    def to_config(self) -> dict[str, Any]:
        config = super().to_config()
        config.update({"label": self.label})
        return config


# Only define the EXTRA fields here. Shared fields (default_on, preparation_state)
# and the led_type dropdown are auto-injected by the extension manager.
CONFIG_FIELDS: dict[str, ConfigInterface] = {
    "label": StringType(default="default"),
}


class Implementation(LedInterface):
    """Custom LED implementation.

    Implement at most these four methods — the base class manages threading,
    cancellation, and the preparation_state switch for you.

    Inherited attributes from LedInterface:
      self.config            — your ExtensionConfig instance
      self.hardware          — HardwareContext with pin_controller, scale,
                               carriage, rfid, and extra (dict of hardware
                               extension instances)
      self.default_on        — whether the LED should be on by default
      self.preparation_state — "On" / "Off" / "Effect" during preparation

    Required:
      turn_on()  — steady idle state
      turn_off() — off state

    Optional (only override if you want animation):
      active_frames()        — generator yielding seconds-to-sleep between
                               frames during a cocktail run.
      end_frames()           — generator yielding seconds-to-sleep between
                               frames after a cocktail finishes; the
                               implementation decides the total duration.

    Optional:
      cleanup() — release driver-specific handles. Pin cleanup is centralised
                  in HardwareContext, so most LEDs do not need this.

    Cancellation: animations are auto-cancelled when a new preparation starts,
    when the controller turns off, or at shutdown. Just yield frames — the
    base class closes the generator and stops the thread for you.
    """

    def __init__(
        self,
        config: ExtensionConfig,
        hardware: HardwareContext,
    ) -> None:
        super().__init__(config, hardware)
        self.label = config.label
        # >>> Initialize your hardware here (e.g. open GPIO, SPI, I2C bus) <<<
        _logger.info(f"LED '{EXTENSION_NAME}' initialized (label={self.label})")

    def turn_on(self) -> None:
        """Turn the LED on."""
        # >>> Drive your hardware on <<<
        _logger.debug(f"LED '{EXTENSION_NAME}' on")

    def turn_off(self) -> None:
        """Turn the LED off."""
        # >>> Drive your hardware off <<<
        _logger.debug(f"LED '{EXTENSION_NAME}' off")

    def active_frames(self) -> Iterator[float]:
        """Heartbeat blink while a cocktail is being prepared.

        The base class drives this generator on a daemon thread, waits for the
        yielded seconds between frames, and closes the generator the moment
        preparation ends, the controller turns off, or the program shuts down.
        Use ``while True`` — you do NOT need to check a stop flag. Yielded
        sleeps can be any duration; the real rule is to keep the work between
        yields non-blocking (no ``time.sleep`` or blocking I/O inside the
        frame body, including inside ``turn_on`` / ``turn_off``).
        """
        while True:
            self.turn_on()
            yield 0.2
            self.turn_off()
            yield 0.2

    def end_frames(self) -> Iterator[float]:
        """Blink at 5 Hz for 5 seconds after preparation finishes.

        Pick whatever duration suits your hardware. The base class still
        cancels the iterator early if a new preparation starts.
        """
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
