from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.interface import SinglePinController

_logger = LoggerHandler("GenericController")

try:
    # pylint: disable=import-error
    from periphery import GPIO
    from periphery.gpio import GPIOError

    DEV = False
except ModuleNotFoundError:
    DEV = True


class GenericGPIO(SinglePinController):
    def __init__(self, pin: int, inverted: bool) -> None:
        self.low = False
        self.high = True
        self.pin = pin
        self.inverted = inverted
        self.devenvironment = DEV
        if inverted:
            self.low, self.high = self.high, self.low
        self.gpio: GPIO | None = None

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        if self.devenvironment:
            _logger.warning(f"Could not import periphery.GPIO. Will not be able to control pin: GPIO-{self.pin}")
            return
        try:
            if is_input:
                self.gpio = GPIO(self.pin, "in", bias="pull_down" if pull_down else "pull_up")
            else:
                init_value = "high" if self.inverted else "out"
                self.gpio = GPIO(self.pin, init_value)
        except GPIOError as e:
            self.devenvironment = True
            _logger.log_exception(e)

    def activate(self) -> None:
        if self.gpio is None:
            return
        self.gpio.write(self.high)

    def close(self) -> None:
        if self.gpio is None:
            return
        self.gpio.write(self.low)

    def cleanup(self) -> None:
        if self.gpio is None:
            return
        self.gpio.close()

    def read(self) -> bool:
        if self.gpio is None:
            return False
        return self.gpio.read()
