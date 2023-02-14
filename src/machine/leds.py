from threading import Thread
import time
from typing import Protocol
from abc import abstractmethod
from random import randint
from src.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.machine.interface import PinController

_logger = LoggerHandler("LedController")

try:
    # pylint: disable=import-error
    from rpi_ws281x import PixelStrip, Color  # type: ignore
    MODULE_AVAILABLE = True
except ModuleNotFoundError:
    MODULE_AVAILABLE = False


class LedController:
    def __init__(self, pin_controller: PinController) -> None:
        self.pin_controller = pin_controller
        self.pins = cfg.MAKER_LED_PINS
        enabled = len(cfg.MAKER_LED_PINS) > 0
        self.controllable = cfg.MAKER_LED_IS_WS and MODULE_AVAILABLE
        if enabled and cfg.MAKER_LED_IS_WS and not MODULE_AVAILABLE:
            _logger.log_event("WARNING", "Could not import rpi_ws281x. Will only be able to use basic light effects")
        self.led_list: list[_LED] = [
            _controllableLED(pin) if self.controllable else _normalLED(pin, self.pin_controller)
            for pin in self.pins
        ]

    def preparation_start(self):
        for led in self.led_list:
            led.preparation_start()

    def preparation_end(self, duration: int = 5):
        for led in self.led_list:
            led.preparation_end(duration)


class _LED(Protocol):
    @abstractmethod
    def preparation_start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def preparation_end(self, duration: int) -> None:
        raise NotImplementedError


class _normalLED(_LED):
    def __init__(self, pin: int, pin_controller: PinController) -> None:
        self.pin = pin
        self.pin_controller = pin_controller
        self.pin_controller.initialize_pin_list([self.pin])

    def __del__(self):
        self.pin_controller.cleanup_pin_list([self.pin])

    def _turn_on(self):
        """Turns the LEDs on"""
        self.pin_controller.activate_pin_list([self.pin])

    def _turn_off(self):
        """Turns the LEDs off"""
        self.pin_controller.close_pin_list([self.pin])

    def preparation_start(self):
        """Plays an effect after the preparation for x seconds"""
        self._turn_on()

    def preparation_end(self, duration: int = 5):
        """Effect during preparation"""
        self._turn_off()
        blinker = Thread(target=self._blink_for, kwargs={"duration": duration})
        blinker.start()

    def _blink_for(self, duration: int = 5, interval: float = 0.1):
        current_time = 0
        while current_time <= duration:
            self._turn_on()
            time.sleep(interval)
            current_time += interval
            self._turn_off()
            time.sleep(interval)
            current_time += interval


class _controllableLED(_LED):
    def __init__(self, pin: int) -> None:
        self.pin = pin
        self.strip = PixelStrip(
            cfg.MAKER_LED_COUNT,
            pin,
            800000,     # freq
            10,         # DMA 5 / 10
            False,      # invert
            255,        # brightness
            1           # channel
        )
        self.strip.begin()
        self.is_preparing = False

    def _preparation_thread(self):
        """Fills one by one with same random color, then repeats / overwrites old ones"""
        wait_ms = 25
        while self.is_preparing:
            color = Color(
                randint(0, 255),
                randint(0, 255),
                randint(0, 255),
            )
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, color)
                self.strip.show()
                time.sleep(wait_ms / 1000)

    def turn_off(self):
        for i in range(0, self.strip.numPixels()):
            self.strip.setPixelColor(i, 0)

    def _wheel(self, pos: int):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        if pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

    def _end_thread(self, duration: int = 5):
        """Rainbow movie theater light style chaser animation."""
        wait_ms = 25
        current_time = 0
        wheel_order = range(256)
        start = randint(0, 255)
        wheel_order = list(wheel_order[start::]) + list(wheel_order[0:start])
        while current_time <= duration:
            for j in wheel_order:
                for k in range(3):
                    for i in range(0, self.strip.numPixels(), 3):
                        self.strip.setPixelColor(i + k, self._wheel((i + j) % 255))
                    self.strip.show()
                    time.sleep(wait_ms / 1000)
                    for i in range(0, self.strip.numPixels(), 3):
                        self.strip.setPixelColor(i + k, 0)
        self.turn_off()

    def preparation_start(self):
        """Effect during preparation"""
        self.is_preparing = True
        cycler = Thread(target=self._preparation_thread)
        cycler.start()

    def preparation_end(self, duration: int = 5):
        """Plays an effect after the preparation for x seconds"""
        self.is_preparing = False
        rainbow = Thread(target=self._end_thread, kwargs={"duration": duration})
        rainbow.start()
