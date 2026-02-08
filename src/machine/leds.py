from __future__ import annotations

import time
from abc import abstractmethod
from random import randint
from threading import Thread
from typing import Protocol

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import NormalLedConfig, WS281xLedConfig
from src.logger_handler import LoggerHandler
from src.machine.interface import PinController

_logger = LoggerHandler("LedController")

try:
    # pylint: disable=import-error
    from rpi_ws281x import Adafruit_NeoPixel, Color  # pyright: ignore[reportMissingImports]

    MODULE_AVAILABLE = True
except ModuleNotFoundError:
    MODULE_AVAILABLE = False


class LedController:
    def __init__(self, pin_controller: PinController) -> None:
        self._pin_controller = pin_controller
        self.led_list: list[_LED] = []

        # Initialize normal LEDs
        for led_config in cfg.LED_NORMAL:
            normal_led: _normalLED = _normalLED(led_config, self._pin_controller)
            self.led_list.append(normal_led)

        # Initialize WS281x LEDs
        if len(cfg.LED_WSLED) > 0:
            if not MODULE_AVAILABLE:
                _logger.log_event(
                    "ERROR",
                    "Could not import rpi_ws281x. Will not be able to control the WS281x, please install the library.",
                )
                return
            try:
                for wsled_config in cfg.LED_WSLED:
                    controllable_led: _controllableLED = _controllableLED(wsled_config)
                    self.led_list.append(controllable_led)
            # Will be thrown if ws281x module init (.begin()) as none root
            except RuntimeError:
                _logger.log_event("ERROR", "Could not set up the WS281x, is the program running as root?")

    def preparation_start(self) -> None:
        for led in self.led_list:
            led.preparation_start()

    def preparation_end(self, duration: int = 5) -> None:
        for led in self.led_list:
            led.preparation_end(duration)

    def default_led(self) -> None:
        for led in self.led_list:
            if led.default_on:
                led.turn_on()

    def turn_off(self) -> None:
        """Turn all LEDs off."""
        for led in self.led_list:
            led.turn_off()


class _LED(Protocol):
    default_on: bool

    @abstractmethod
    def preparation_start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def preparation_end(self, duration: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def turn_on(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def turn_off(self) -> None:
        raise NotImplementedError


class _normalLED(_LED):
    def __init__(self, config: NormalLedConfig, _pin_controller: PinController) -> None:
        self.pin = config.pin
        self.default_on = config.default_on
        self.preparation_state = config.preparation_state
        self._pin_controller = _pin_controller
        self._pin_controller.initialize_pin_list([self.pin])

    def __del__(self) -> None:
        self._pin_controller.cleanup_pin_list([self.pin])

    def turn_on(self) -> None:
        """Turn the LEDs on."""
        self._pin_controller.activate_pin_list([self.pin])

    def turn_off(self) -> None:
        """Turn the LEDs off."""
        self._pin_controller.close_pin_list([self.pin])

    def preparation_start(self) -> None:
        """Turn the LED on during preparation."""
        if self.preparation_state in ("On", "Effect"):
            self.turn_on()
        else:
            self.turn_off()

    def preparation_end(self, duration: int = 5) -> None:
        """Blink for some time after preparation."""
        if self.preparation_state == "Effect":
            self.turn_off()
            blinker = Thread(target=self._blink_for, kwargs={"duration": duration})
            blinker.daemon = True
            blinker.start()
        elif self.default_on:
            self.turn_on()
        else:
            self.turn_off()

    def _blink_for(self, duration: int = 5, interval: float = 0.2) -> None:
        current_time = 0.0
        step = interval / 2
        while current_time <= duration:
            self.turn_on()
            time.sleep(step)
            current_time += step
            self.turn_off()
            time.sleep(step)
            current_time += step
        if self.default_on:
            self.turn_on()


class _controllableLED(_LED):
    def __init__(self, config: WS281xLedConfig) -> None:
        self.pin = config.pin
        self.brightness = min(int(255 * config.brightness / 100), 255)
        self.count = config.count
        self.number_rings = config.number_rings
        self.default_on = config.default_on
        self.preparation_state = config.preparation_state
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
        self.is_preparing = False

    def _preparation_thread(self) -> None:
        """Fill one by one with same random color, then repeats / overwrites old ones."""
        # Make the circle / dot approximate 2 rounds per second
        wait_ms = 500 / self.count
        # not faster than 10ms
        wait_ms = max(10, wait_ms)
        self.turn_on(Color(randint(0, 255), randint(0, 255), randint(0, 255)))
        while self.is_preparing:
            color = Color(
                randint(0, 255),
                randint(0, 255),
                randint(0, 255),
            )
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
                time.sleep(wait_ms / 1000)

    def turn_off(self) -> None:
        """Turn all leds off."""
        for k in range(self.number_rings):
            for i in range(self.count):
                iter_pos = k * self.count + i
                self.strip.setPixelColor(iter_pos, Color(0, 0, 0))
        self.strip.show()

    def turn_on(self, color: None | Color = None) -> None:
        """Turn all leds on to given color."""
        if color is None:
            color = Color(255, 255, 255)
        for k in range(self.number_rings):
            for i in range(self.count):
                iter_pos = k * self.count + i
                self.strip.setPixelColor(iter_pos, color)
        self.strip.show()

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

    def _end_thread(self, duration: int = 5) -> None:
        """Rainbow animation fades across all pixels at once."""
        wait_ms = 10.0
        current_time = 0.0
        wheel_order = list(range(256))
        start = randint(0, 255)
        wheel_order = wheel_order[start::] + wheel_order[0:start]
        while current_time <= duration:
            for j in wheel_order:
                for i in range(self.count):
                    for k in range(self.number_rings):
                        iter_pos = k * self.count + i
                        self.strip.setPixelColor(iter_pos, self._wheel((i + j) & 255))
                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                current_time += wait_ms / 1000.0
                # break out of loop (its long) when we are finished
                if current_time > duration:
                    break
        if self.default_on:
            self.turn_on()
        else:
            self.turn_off()

    def preparation_start(self) -> None:
        """Effect during preparation."""
        if self.preparation_state == "Effect":
            self.is_preparing = True
            cycler = Thread(target=self._preparation_thread)
            cycler.daemon = True
            cycler.start()
        elif self.preparation_state == "On":
            self.turn_on()
        else:
            self.turn_off()

    def preparation_end(self, duration: int = 5) -> None:
        """Plays an effect after the preparation for x seconds."""
        if self.preparation_state == "Effect":
            self.is_preparing = False
            rainbow = Thread(target=self._end_thread, kwargs={"duration": duration})
            rainbow.daemon = True
            rainbow.start()
        elif self.default_on:
            self.turn_on()
        else:
            self.turn_off()
