from typing import Literal, Optional

from src.logger_handler import LoggerHandler
from src.machine.interface import GPIOController, PinController

logger = LoggerHandler("RpiController")

try:
    # pylint: disable=import-error
    from RPi import GPIO  # type: ignore

    GPIO.setmode(GPIO.BCM)
    DEV = False
except ModuleNotFoundError:
    DEV = True


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
            print(f"Devenvironment on the RPi module is {'on' if self.devenvironment else 'off'}")
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

    def cleanup_pin_list(self, pin_list: Optional[list[int]] = None):
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
