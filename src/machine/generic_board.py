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

    def __init__(self) -> None:
        super().__init__()
        self.devenvironment = DEV
        self.gpios: dict[int, GPIO] = {}

    def initialize_pin_list(self, pin_list: List[int]):
        """Set up the given pin list"""
        print(f"Devenvironment on the Generic Pin Control module is {'on' if self.devenvironment else 'off'}")
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin] = GPIO(pin, "out")
        else:
            logger.log_event("WARNING", "Could not import periphery.GPIO. Will not be able to control pins")
            logger.log_event("WARNING", "Try to install python-periphery and run program as root.")

    def activate_pin_list(self, pin_list: List[int]):
        """Activates the given pin list"""
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin].write(True)

    def close_pin_list(self, pin_list: List[int]):
        """Closes the given pin_list"""
        if not self.devenvironment:
            for pin in pin_list:
                self.gpios[pin].write(False)

    def cleanup_pin_list(self, pin_list: Optional[List[int]] = None):
        if self.devenvironment:
            return
        if pin_list is None:
            for pin in self.gpios.values():
                pin.close()
        else:
            for pin in pin_list:
                self.gpios[pin].close()
