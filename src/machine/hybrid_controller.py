"""Hybrid PinController that wraps individual SinglePin instances.

This module provides a PinController implementation that supports
mixed pin types (GPIO, MCP23017, PCF8574) in the same machine configuration.
"""

from __future__ import annotations

from src.config.config_types import PumpConfig
from src.logger_handler import LoggerHandler
from src.machine.interface import PinController, SinglePin
from src.machine.pin_factory import PinControllerFactory

_logger = LoggerHandler("HybridPinController")


class HybridPinController(PinController):
    """PinController that wraps individual SinglePin instances.

    This enables mixing different pin types (GPIO, MCP23017, PCF8574)
    in the same machine configuration. Each pin is controlled independently
    through its own SinglePin implementation.
    """

    def __init__(self, inverted: bool) -> None:
        """Initialize the hybrid controller.

        Args:
            inverted: Global pin inversion setting.

        """
        self.inverted = inverted
        self._factory = PinControllerFactory(inverted)
        self._pins: dict[int, SinglePin] = {}  # Maps pin number to SinglePin
        self._dev_displayed = False

    def initialize_pin_list(
        self,
        pin_list: list[int],
        is_input: bool = False,
        pull_down: bool = True,
    ) -> None:
        """Initialize pins based on pump configuration.

        Args:
            pin_list: List of pin numbers to initialize.
            is_input: True for input pins, False for output pins.
            pull_down: True for pull-down resistor, False for pull-up.

        """
        from src.config.config_manager import CONFIG as cfg

        if not self._dev_displayed:
            _logger.info("<i> Using HybridPinController for mixed pin types")
            self._dev_displayed = True

        # Build pin to pump config mapping from active pump configurations
        pump_configs = cfg.PUMP_CONFIG[: cfg.MAKER_NUMBER_BOTTLES]
        pin_to_config: dict[int, PumpConfig] = {pc.pin: pc for pc in pump_configs}

        for pin in pin_list:
            if pin in self._pins:
                continue  # Already initialized

            pump_config = pin_to_config.get(pin)
            if pump_config is None:
                # Pin not in pump config - could be LED, reverter, etc.
                # Create as GPIO by default
                pump_config = PumpConfig(pin=pin, volume_flow=0, tube_volume=0, pin_type="GPIO")

            single_pin = self._factory.create_pin(pump_config)
            single_pin.initialize(is_input, pull_down)
            self._pins[pin] = single_pin
            _logger.debug(f"Initialized pin {pin} as {pump_config.pin_type}")

    def activate_pin_list(self, pin_list: list[int]) -> None:
        """Activate the given pins.

        Args:
            pin_list: List of pin numbers to activate.

        """
        for pin in pin_list:
            if pin in self._pins:
                self._pins[pin].activate()

    def close_pin_list(self, pin_list: list[int]) -> None:
        """Close the given pins.

        Args:
            pin_list: List of pin numbers to close.

        """
        for pin in pin_list:
            if pin in self._pins:
                self._pins[pin].close()

    def cleanup_pin_list(self, pin_list: list[int] | None = None) -> None:
        """Cleanup the given pins or all pins.

        Args:
            pin_list: List of pin numbers to cleanup, or None for all pins.

        """
        if pin_list is None:
            for single_pin in self._pins.values():
                single_pin.cleanup()
            self._pins.clear()
        else:
            for pin in pin_list:
                if pin in self._pins:
                    self._pins[pin].cleanup()
                    del self._pins[pin]

    def read_pin(self, pin: int) -> bool:
        """Read the state of a pin.

        Args:
            pin: The pin number to read.

        Returns:
            True if pin is high, False if low or not initialized.

        """
        if pin in self._pins:
            return self._pins[pin].read()
        return False
