from __future__ import annotations

from typing import TYPE_CHECKING, Self

from src.logger_handler import LoggerHandler

if TYPE_CHECKING:
    from src.machine.leds.base import LedInterface

_logger = LoggerHandler("LedController")


class LedController:
    """Singleton facade around all configured :class:`LedInterface` instances.

    The concrete LED list is wired in by ``MachineController.init_machine()``
    via :meth:`attach`. Callers can hold a reference to ``LedController()``
    even before the machine is initialized — :attr:`led_list` simply stays
    empty until LEDs are attached.
    """

    _instance: Self | None = None

    def __new__(cls) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.led_list: list[LedInterface] = []
        self._initialized = True

    def attach(self, leds: list[LedInterface]) -> None:
        """Replace the active LED list. Pass ``[]`` to detach."""
        self.led_list = leds

    def preparation_start(self) -> None:
        for led in self.led_list:
            led.preparation_start()

    def preparation_end(self) -> None:
        for led in self.led_list:
            led.preparation_end()

    def default_led(self) -> None:
        for led in self.led_list:
            if led.default_on:
                led.turn_on()

    def turn_off(self) -> None:
        """Turn all LEDs off."""
        for led in self.led_list:
            led.turn_off()

    def cleanup(self) -> None:
        """Release per-LED hardware handles. Pin cleanup is handled centrally by HardwareContext."""
        for led in self.led_list:
            try:
                led.cleanup()
            except Exception:
                _logger.log_exception("LED cleanup failure")
