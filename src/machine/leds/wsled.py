# pyright: reportMissingImports=false
from __future__ import annotations

from collections.abc import Iterator
from random import randint
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.leds.base import LedInterface

if TYPE_CHECKING:
    from src.config.config_types import WS281xLedConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("WSLed")

_NOT_AVAILABLE_MSG = "Could not import rpi_ws281x. Will not be able to control the WS281x, please install the library."

try:
    from rpi_ws281x import Adafruit_NeoPixel, Color  # pyright: ignore[reportMissingImports]

    WS281X_AVAILABLE = True
except ModuleNotFoundError:
    WS281X_AVAILABLE = False


class WSLed(LedInterface):
    """Addressable WS281x / NeoPixel LED ring (or chained rings) on GPIO."""

    def __init__(self, config: WS281xLedConfig, hardware: HardwareContext) -> None:
        super().__init__(config, hardware)
        if not WS281X_AVAILABLE:
            raise RuntimeError(_NOT_AVAILABLE_MSG)
        self.pin = config.pin
        self.brightness = min(int(255 * config.brightness / 100), 255)
        self.count = config.count
        self.number_rings = config.number_rings
        self.strip = Adafruit_NeoPixel(
            self.count * self.number_rings,
            self.pin,  # best to use 12 or 18
            800000,  # freq
            10,  # DMA 5 / 10
            False,  # invert
            self.brightness,  # brightness
            0,  # channel 0 or 1
        )
        # will throw a RuntimeError as none root user here
        self.strip.begin()

    def turn_off(self) -> None:
        """Turn all leds off."""
        self._paint(Color(0, 0, 0))

    def turn_on(self) -> None:
        """Turn all leds on with a neutral white."""
        self._paint(Color(255, 255, 255))

    def _paint(self, color: Color) -> None:
        """Set every pixel of every ring to ``color`` and push to the strip."""
        for k in range(self.number_rings):
            for i in range(self.count):
                iter_pos = k * self.count + i
                self.strip.setPixelColor(iter_pos, color)
        self.strip.show()

    def active_frames(self) -> Iterator[float]:
        """Spinner-like fill cycle in a random colour, refreshed each lap."""
        # Make the circle / dot approximate 2 rounds per second
        wait_s = max(0.01, 0.5 / self.count)
        self._paint(Color(randint(0, 255), randint(0, 255), randint(0, 255)))
        while True:
            color = Color(randint(0, 255), randint(0, 255), randint(0, 255))
            for i in range(self.count):
                # If multiple identical ring LEDs operate them simultaneously
                for k in range(self.number_rings):
                    iter_pos = k * self.count + i
                    self.strip.setPixelColor(iter_pos, color)
                    # Turn of 2 leading LEDs to have a more spinner like light effect
                    of_pos = iter_pos + 1 if i != self.count - 1 else 0 + k * self.count
                    of_pos2 = iter_pos + 2 if i != self.count - 2 else 0 + k * self.count
                    self.strip.setPixelColor(of_pos, Color(0, 0, 0))
                    self.strip.setPixelColor(of_pos2, Color(0, 0, 0))
                self.strip.show()
                yield wait_s

    def end_frames(self) -> Iterator[float]:
        """Rainbow animation fading across all pixels for 5 seconds."""
        wait_s = 0.01
        duration = 5.0
        elapsed = 0.0
        wheel_order = list(range(256))
        start = randint(0, 255)
        wheel_order = wheel_order[start::] + wheel_order[0:start]
        while elapsed <= duration:
            for j in wheel_order:
                for i in range(self.count):
                    for k in range(self.number_rings):
                        iter_pos = k * self.count + i
                        self.strip.setPixelColor(iter_pos, self._wheel((i + j) & 255))
                self.strip.show()
                yield wait_s
                elapsed += wait_s
                if elapsed > duration:
                    return

    def _wheel(self, pos: int) -> Color:
        """Generate rainbow colors across 0-255 positions."""
        first_section = 85
        second_section = 170
        max_position = 255
        if pos < first_section:
            return Color(pos * 3, max_position - pos * 3, 0)
        if pos < second_section:
            pos -= first_section
            return Color(max_position - pos * 3, 0, pos * 3)
        pos -= second_section
        return Color(0, pos * 3, max_position - pos * 3)
