from __future__ import annotations

import contextlib
from typing import Literal

from src.logger_handler import LoggerHandler
from src.machine.interface import GPIOController, PinController
from src.utils import time_print

logger = LoggerHandler("RpiController")

try:
    # pylint: disable=import-error
    from RPi import GPIO  # type: ignore

    GPIO.setmode(GPIO.BCM)
    DEV = False
except ModuleNotFoundError:
    DEV = True

try:
    # pylint: disable=import-error
    from gpiozero import InputDevice, OutputDevice  # type: ignore

    ZERO_DEV = False
except ModuleNotFoundError:
    ZERO_DEV = True


def is_rpi5() -> bool:
    model = "No Model"
    with contextlib.suppress(FileNotFoundError), open("/proc/device-tree/model", encoding="utf-8") as f:
        model = f.read()
    return "Raspberry Pi 5" in model


def choose_pi_controller(inverted: bool) -> PinController:
    """Need to choose another controller for Raspberry Pi 5."""
    if is_rpi5():
        return Rpi5Controller(inverted)
    return RpiController(inverted)


class RpiController(PinController):
    """Controller class to control Raspberry Pi pins."""

    def __init__(self, inverted: bool) -> None:
        super().__init__()
        self.inverted = inverted
        self.devenvironment = DEV
        self.low: Literal[0, 1] = GPIO.LOW if not DEV else 0
        self.high: Literal[0, 1] = GPIO.HIGH if not DEV else 1
        if inverted:
            self.low, self.high = self.high, self.low
        self.dev_displayed = False

    def initialize_pin_list(self, pin_list: list[int], is_input: bool = False, pull_down: bool = True):
        """Set up the given pin list."""
        if not self.dev_displayed:
            time_print(f"Devenvironment on the RPi module is {'on' if self.devenvironment else 'off'}")
            self.dev_displayed = True
        if not self.devenvironment:
            # if it is an input, we need to set the pull up down to down or up
            # depending on how the input sensor works
            # otherwise the jitter may emit false signals
            if is_input:
                pull_up_down = GPIO.PUD_DOWN if pull_down else GPIO.PUD_UP
                GPIO.setup(pin_list, GPIO.IN, pull_up_down=pull_up_down)
            else:
                GPIO.setup(pin_list, GPIO.OUT, initial=self.low)
        else:
            logger.log_event("WARNING", f"Could not import RPi.GPIO. Will not be able to control pins: {pin_list}")

    def activate_pin_list(self, pin_list: list[int]):
        """Activates the given pin list."""
        if not self.devenvironment:
            GPIO.output(pin_list, self.high)

    def close_pin_list(self, pin_list: list[int]):
        """Close the given pin_list."""
        if not self.devenvironment:
            GPIO.output(pin_list, self.low)

    def cleanup_pin_list(self, pin_list: list[int] | None = None):
        """Clean up the given pin list, or all pins if none is given."""
        if self.devenvironment:
            return
        if pin_list is None:
            GPIO.cleanup()
        else:
            GPIO.cleanup(pin_list)

    def read_pin(self, pin: int) -> bool:
        """Return the state of the given pin."""
        if not self.devenvironment:
            return GPIO.input(pin) == GPIO.HIGH
        return False


class Rpi5Controller(PinController):
    """Controller class to control Raspberry Pi pins using gpiozero."""

    def __init__(self, inverted: bool) -> None:
        super().__init__()
        self.inverted = inverted
        self.devenvironment = ZERO_DEV
        self.low: bool = False
        self.high: bool = True
        if inverted:
            self.low, self.high = self.high, self.low
        self.active_high = not inverted  # Control active_high based on the inverted parameter
        self.gpios: dict[
            int, InputDevice | OutputDevice
        ] = {}  # Dictionary to store GPIO pin objects (InputDevice/OutputDevice)
        self.dev_displayed = False

    def initialize_pin_list(self, pin_list: list[int], is_input: bool = False, pull_down: bool = True):
        """Set up the given pin list using gpiozero with error handling."""
        if not self.dev_displayed:
            time_print(f"Devenvironment on the RPi5 module is {'on' if self.devenvironment else 'off'}")
            self.dev_displayed = True

        if self.devenvironment:
            logger.log_event("WARNING", f"Could not import gpiozero. Will not be able to control pins: {pin_list}")
            return
        for pin in pin_list:
            try:
                if is_input:
                    # Set pull-up/down configuration via InputDevice
                    pull_up = not pull_down
                    self.gpios[pin] = InputDevice(pin, pull_up=pull_up)
                else:
                    # Initialize OutputDevice with active_high based on the inverted flag
                    self.gpios[pin] = OutputDevice(pin, initial_value=self.low, active_high=self.active_high)
            except Exception as e:
                # Catch any error and continue, printing the pin and error message
                logger.log_event("WARNING", f"Error: Could not initialize GPIO pin {pin}. Reason: {e!s}")

    def activate_pin_list(self, pin_list: list[int]):
        """Activates the given pin list (sets to high)."""
        if self.devenvironment:
            return
        for pin in pin_list:
            if pin in self.gpios and isinstance(self.gpios[pin], OutputDevice):
                self.gpios[pin].on()
            else:
                logger.log_event(
                    "WARNING", f"Could not activate GPIO pin {pin}. Reason: Pin not activated or not an OutputDevice."
                )

    def close_pin_list(self, pin_list: list[int]):
        """Close (deactivate) the given pin_list (sets to low)."""
        if self.devenvironment:
            return
        for pin in pin_list:
            if pin in self.gpios and isinstance(self.gpios[pin], OutputDevice):
                self.gpios[pin].off()

    def cleanup_pin_list(self, pin_list: list[int] | None = None):
        """Clean up the given pin list, or all pins if none is given."""
        if pin_list is None:
            # Clean up all pins
            for pin, device in self.gpios.items():
                device.close()
            self.gpios.clear()
        else:
            for pin in pin_list:
                if pin in self.gpios:
                    self.gpios[pin].close()
                    del self.gpios[pin]

    def read_pin(self, pin: int) -> bool:
        """Return the state of the given pin (True if high, False if low)."""
        if pin in self.gpios and isinstance(self.gpios[pin], InputDevice):
            return self.gpios[pin].is_active  # True if high, False if low
        logger.log_event("WARNING", f"Could not read GPIO pin {pin}. Reason: Pin not found or not an InputDevice.")
        return False


class RaspberryGPIO(GPIOController):
    def __init__(self, inverted: bool, pin: int):
        low = GPIO.LOW if not DEV else 0
        high = GPIO.HIGH if not DEV else 1
        super().__init__(high, low, inverted, pin)

    def initialize(self):
        GPIO.setup(self.pin, GPIO.OUT, initial=self.low)

    def activate(self):
        GPIO.output(self.pin, self.high)

    def close(self):
        GPIO.output(self.pin, self.low)

    def cleanup(self):
        GPIO.cleanup(self.pin)
