from typing import List
from src.machine.interface import PinController
from src.logger_handler import LoggerHandler, LogFiles


logger = LoggerHandler("RpiController", LogFiles.PRODUCTION)

try:
    # pylint: disable=import-error
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    DEV = False
except ModuleNotFoundError:
    DEV = True
    logger.log_event("WARNING", "Could not import RPi.GPIO. Will not be able to control pins")


class RpiController(PinController):
    """Controller class to control Raspberry Pi pins"""

    def __init__(self) -> None:
        super().__init__()
        self.devenvironment = DEV

    def initialize_pin_list(self, pin_list: List[int]):
        """Set up the given pin list"""
        print(f"Devenvironment on the RPi module is {'on' if self.devenvironment else 'off'}")
        if not self.devenvironment:
            for pin in pin_list:
                GPIO.setup(pin, 0)
                GPIO.output(pin, 1)

    def activate_pin_list(self, pin_list: List[int]):
        """Activates the given pin list"""
        if not self.devenvironment:
            for pin in pin_list:
                GPIO.output(pin, 0)

    def close_pin_list(self, pin_list: List[int]):
        """Closes the given pin_list"""
        if not self.devenvironment:
            for pin in pin_list:
                GPIO.output(pin, 1)
