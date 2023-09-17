"""Module to create the according GPIO controller for the appropriate Board"""
from typing import Any
from src.machine.interface import GPIOController
from src.config_manager import CONFIG as cfg


try:
    # pylint: disable=import-error
    from RPi import GPIO as rpi_GPIO  # type: ignore
    rpi_GPIO.setmode(rpi_GPIO.BCM)
    rpi_GPIO.setwarnings(False)
    RPI_DEV = False
except ModuleNotFoundError:
    RPI_DEV = True

try:
    # pylint: disable=import-error
    from periphery import GPIO as p_GPIO  # type: ignore
    P_DEV = False
except ModuleNotFoundError:
    P_DEV = True


class GPIOFactory:
    def __init__(self, inverted: bool) -> None:
        # global general inverted status
        self.inverted = inverted
        # flag if the import warning was already triggered,
        # used to prevent the warning multiple times
        self.import_warning = False
        self.generic_high = True
        self.generic_low = False
        self.rpi_high = rpi_GPIO.HIGH if not RPI_DEV else 1
        self.rpi_low = rpi_GPIO.LOW if not RPI_DEV else 0

    def generate_gpio(self, inverted: bool, pin: int) -> GPIOController:
        """Return the appropriate GPIO
        Option to specific invert one GPIO relative to general setting
        """
        board = cfg.MAKER_BOARD
        # using xor here to created the right inverted status
        is_inverted = self.inverted ^ inverted
        if board == "RPI":
            return RaspberryGPIO(1, 0, is_inverted, pin)
        else:
            return GenericGPIO(1, 0, is_inverted, pin)


class GenericGPIO(GPIOController):
    def __init__(
        self,
        high: Any,
        low: Any,
        inverted: bool,
        pin: int
    ):
        super().__init__(high, low, inverted, pin)
        self.gpio = None

    def initialize(self):
        init_value = "high" if self.inverted else "out"
        self.gpio = p_GPIO(self.pin, init_value)

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


class RaspberryGPIO(GPIOController):
    def initialize(self):
        rpi_GPIO.setup(self.pin, rpi_GPIO.OUT, initial=self.low)

    def activate(self):
        rpi_GPIO.output(self.pin, self.high)

    def close(self):
        rpi_GPIO.output(self.pin, self.low)

    def cleanup(self):
        rpi_GPIO.cleanup(self.pin)
