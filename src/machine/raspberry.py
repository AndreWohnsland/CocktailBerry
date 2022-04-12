from typing import List
from src.machine.interface import PinController
from src.logger_handler import LoggerHandler


logger = LoggerHandler("RpiController", "production_logs")

try:
    # pylint: disable=import-error
    from RPi import GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    DEV = False
except ModuleNotFoundError:
    DEV = True
    logger.log_event("WARNING", "Could not import RPi.GPIO. Will not be able to controll pins")


class RpiController(PinController):
    def __init__(self) -> None:
        self.devenvironment = DEV

    def initialize_pinlist(self, pinlist: List[int]):
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.setup(pin, 0)
                GPIO.output(pin, 1)

    def activate_pinlist(self, pinlist: List[int]):
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.output(pin, 0)

    def close_pinlist(self, pinlist: List[int]):
        if not self.devenvironment:
            for pin in pinlist:
                GPIO.output(pin, 1)
