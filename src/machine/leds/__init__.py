from __future__ import annotations

from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.leds.base import LedInterface
from src.machine.leds.controller import LedController
from src.machine.leds.normal import NormalLed
from src.machine.leds.wsled import WSLed

if TYPE_CHECKING:
    from src.config.config_types import BaseLedConfig
    from src.machine.hardware import HardwareContext

_logger = LoggerHandler("leds")

__all__ = ["LedController", "LedInterface", "NormalLed", "WSLed", "create_led_controller"]


def create_led_controller(config_list: list[BaseLedConfig], hardware: HardwareContext) -> LedController:
    """Build all configured LEDs and attach them to the :class:`LedController` singleton.

    Every LED — built-in or from ``addons/leds/`` — receives the full
    ``HardwareContext`` so it can reach pins, scale, carriage, RFID, or
    hardware extension instances if needed. Failed LEDs are skipped with a
    warning so a single misconfigured entry does not disable the whole list.
    """
    from src.config.config_types import NormalLedConfig, WS281xLedConfig

    controller = LedController()
    leds: list[LedInterface] = []
    for config in config_list:
        try:
            if isinstance(config, NormalLedConfig):
                leds.append(NormalLed(config, hardware))
                continue
            if isinstance(config, WS281xLedConfig):
                leds.append(WSLed(config, hardware))
                continue
            # Custom LED extensions from addons/leds/ — dispatch by led_type.
            from src.programs.addons.led_extensions import LED_ADDONS

            entry = LED_ADDONS.entries.get(config.led_type)
            if entry is not None:
                leds.append(entry.implementation_class(config, hardware))
                continue
            _logger.error(f"Unknown led type: {config.led_type}")
        except Exception:
            _logger.warning(f"LED initialization failed for type '{config.led_type}', skipping entry")
            _logger.log_exception("LED initialization traceback")
    controller.attach(leds)
    return controller
