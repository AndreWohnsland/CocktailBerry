from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Literal

from src.logger_handler import LoggerHandler
from src.machine.interface import SinglePinController

_logger = LoggerHandler("RpiController")

try:
    # pylint: disable=import-error
    from RPi import GPIO  # pyright: ignore[reportMissingModuleSource]

    GPIO.setmode(GPIO.BCM)
    DEV = False
except (ModuleNotFoundError, RuntimeError):
    DEV = True

try:
    # pylint: disable=import-error
    from gpiozero import (  # pyright: ignore[reportMissingImports, reportMissingModuleSource]
        InputDevice,
        OutputDevice,
    )

    ZERO_DEV = False
except (ModuleNotFoundError, RuntimeError):
    ZERO_DEV = True


def is_rpi5() -> bool:
    model = "No Model"
    with contextlib.suppress(FileNotFoundError), Path("/proc/device-tree/model").open(encoding="utf-8") as f:
        model = f.read()
    return "raspberry pi 5" in model.lower()


def is_rpi() -> bool:
    """Check if the current machine is a Raspberry Pi."""
    model = "No Model"
    with contextlib.suppress(FileNotFoundError), Path("/proc/device-tree/model").open(encoding="utf-8") as f:
        model = f.read()
    return "raspberry pi" in model.lower()


class RaspberryGPIO(SinglePinController):
    def __init__(self, pin: int, inverted: bool) -> None:
        self.low: Literal[0, 1] = 0
        self.high: Literal[0, 1] = 1
        self.pin = pin
        self.inverted = inverted
        self.devenvironment = DEV
        if inverted:
            self.low, self.high = self.high, self.low

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        if self.devenvironment:
            _logger.warning(f"Could not import RPi.GPIO. Will not be able to control pin: GPIO-{self.pin}")
            return
        if is_input:
            pull_up_down = GPIO.PUD_DOWN if pull_down else GPIO.PUD_UP
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull_up_down)
        else:
            GPIO.setup(self.pin, GPIO.OUT, initial=self.low)

    def activate(self) -> None:
        if not self.devenvironment:
            GPIO.output(self.pin, self.high)

    def close(self) -> None:
        if not self.devenvironment:
            GPIO.output(self.pin, self.low)

    def cleanup(self) -> None:
        if not self.devenvironment:
            GPIO.cleanup(self.pin)

    def read(self) -> bool:
        if not self.devenvironment:
            return GPIO.input(self.pin) == GPIO.HIGH
        return False


class Rpi5GPIO(SinglePinController):
    def __init__(self, pin: int, inverted: bool) -> None:
        self.pin = pin
        self.inverted = inverted
        self.devenvironment = ZERO_DEV
        self.active_high = not inverted
        self._output: OutputDevice | None = None
        self._input: InputDevice | None = None

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        if self.devenvironment:
            _logger.warning(f"Could not import gpiozero. Will not be able to control pin: GPIO-{self.pin}")
            return
        try:
            if is_input:
                pull_up = not pull_down
                self._input = InputDevice(self.pin, pull_up=pull_up)
            else:
                self._output = OutputDevice(self.pin, initial_value=False, active_high=self.active_high)
        except Exception as e:
            _logger.warning(f"Error: Could not initialize pin GPIO-{self.pin}. Reason: {e!s}")

    def activate(self) -> None:
        if self._output is None:
            return
        self._output.on()

    def close(self) -> None:
        if self._output is None:
            return
        self._output.off()

    def cleanup(self) -> None:
        if self._output is not None:
            self._output.close()
            self._output = None
        if self._input is not None:
            self._input.close()
            self._input = None

    def read(self) -> bool:
        if self._input is None:
            return False
        return self._input.is_active
