from typing import List, Optional
from src.machine.interface import PinController
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
        print(f"Devenvironment on the Generic Pin Control module is {'on' if self.devenvironment else 'off'}")

    def initialize_pin_list(self, pin_list: List[int]):
        """Set up the given pin list"""
        init_value = "high" if self.inverted else "out"
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin] = GPIO(pin, init_value)
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
        if self.devenvironment:
            return
        if pin_list is None:
            for pin in self.gpios.values():
                pin.close()
        else:
            for pin in pin_list:
                self.gpios[pin].close()
