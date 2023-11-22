from typing import List, Optional
from src.machine.interface import PinController, GPIOController
from src.logger_handler import LoggerHandler


logger = LoggerHandler("GenericController")

try:
    # pylint: disable=import-error
    from periphery import GPIO  # type: ignore
    DEV = False
except ModuleNotFoundError:
    DEV = True


class GenericController(PinController):
    """Controller class to control pins on a generic board"""

    def __init__(self, inverted: bool) -> None:
        super().__init__()
        self.inverted = inverted
        self.devenvironment = DEV
        self.low = False
        self.high = True
        if inverted:
            self.low, self.high = self.high, self.low
        self.gpios: dict[int, GPIO] = {}
        self.dev_displayed = False

    def initialize_pin_list(self, pin_list: List[int], is_input: bool = False, pull_down: bool = True):
        """Set up the given pin list"""
        if not self.dev_displayed:
            print(f"Devenvironment on the Generic Pin Control module is {'on' if self.devenvironment else 'off'}")
            self.dev_displayed = True

        # high is also output, but other default value
        init_value = "high" if self.inverted else "out"
        # need to change to in if input is true
        # also add the bias (pull down or up)
        add_args = {}
        if is_input:
            init_value = "in"
            add_args["bias"] = "pull_down" if pull_down else "pull_up"
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin] = GPIO(pin, init_value, **add_args)
        else:
            logger.log_event("WARNING", "Could not import periphery.GPIO. Will not be able to control pins")
            logger.log_event("WARNING", "Try to install python-periphery and run program as root.")

    def activate_pin_list(self, pin_list: List[int]):
        """Activates the given pin list"""
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin].write(self.high)

    def close_pin_list(self, pin_list: List[int]):
        """Closes the given pin_list"""
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin].write(self.low)

    def cleanup_pin_list(self, pin_list: Optional[List[int]] = None):
        """Clean up the given pin list, or all pins if none is given"""
        if self.devenvironment:
            return
        if pin_list is None:
            for pin in self.gpios.values():
                pin.close()
        else:
            for pin_number in pin_list:
                self.gpios[pin_number].close()

    def read_pin(self, pin: int) -> bool:
        """Returns the state of the given pin"""
        if not self.devenvironment:
            return self.gpios[pin].read()
        return False


class GenericGPIO(GPIOController):
    def __init__(
        self,
        inverted: bool,
        pin: int
    ):
        low = False
        high = True
        super().__init__(high, low, inverted, pin)
        self.gpio = None

    def initialize(self):
        init_value = "high" if self.inverted else "out"
        self.gpio = GPIO(self.pin, init_value)

    def activate(self):
        if self.gpio is None:
            return
        self.gpio.write(self.high)

    def close(self):
        if self.gpio is None:
            return
        self.gpio.write(self.low)

    def cleanup(self):
        if self.gpio is None:
            return
        self.gpio.close()
