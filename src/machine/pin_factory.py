"""Factory for creating SinglePin instances based on pump configuration.

This module provides a factory class that creates the appropriate SinglePin
implementation based on the pin type specified in the pump configuration.
"""

from __future__ import annotations

from src.config.config_types import PumpConfig
from src.logger_handler import LoggerHandler
from src.machine.interface import SinglePin

_logger = LoggerHandler("PinFactory")


class PinControllerFactory:
    """Factory for creating SinglePin instances based on pump configuration.

    This factory determines the appropriate SinglePin implementation to use
    based on the pin_type field in the PumpConfig and creates instances
    with the correct configuration.
    """

    def __init__(self, inverted: bool) -> None:
        """Initialize the factory.

        Args:
            inverted: Global pin inversion setting.

        """
        self.inverted = inverted

    def create_pin(self, pump_config: PumpConfig) -> SinglePin:
        """Create a SinglePin instance based on pump configuration.

        Args:
            pump_config: The pump configuration containing pin and pin_type.

        Returns:
            A SinglePin instance appropriate for the pin type.

        """
        pin_type = pump_config.pin_type
        pin = pump_config.pin

        if pin_type == "MCP23017":
            return self._create_mcp23017_pin(pin)
        if pin_type == "PCF8574":
            return self._create_pcf8574_pin(pin)
        # GPIO (default)
        return self._create_gpio_pin(pin)

    def _create_gpio_pin(self, pin: int) -> SinglePin:
        """Create a native GPIO SinglePin.

        Automatically selects the appropriate implementation based on
        the detected hardware (RPi, RPi5, or generic).
        """
        from src.machine.generic_board import GenericSinglePin
        from src.machine.raspberry import Rpi5SinglePin, RpiSinglePin, is_rpi, is_rpi5

        if is_rpi():
            if is_rpi5():
                return Rpi5SinglePin(pin, self.inverted)
            return RpiSinglePin(pin, self.inverted)
        return GenericSinglePin(pin, self.inverted)

    def _create_mcp23017_pin(self, pin: int) -> SinglePin:
        """Create an MCP23017 SinglePin."""
        from src.config.config_manager import CONFIG as cfg
        from src.machine.i2c_expander import MCP23017Pin

        address = cfg.MCP23017_CONFIG.address
        return MCP23017Pin(pin, address, self.inverted)

    def _create_pcf8574_pin(self, pin: int) -> SinglePin:
        """Create a PCF8574 SinglePin."""
        from src.config.config_manager import CONFIG as cfg
        from src.machine.i2c_expander import PCF8574Pin

        address = cfg.PCF8574_CONFIG.address
        return PCF8574Pin(pin, address, self.inverted)

    def create_pin_map(self, pump_configs: list[PumpConfig]) -> dict[int, SinglePin]:
        """Create a mapping of bottle numbers (1-indexed) to SinglePin instances.

        Args:
            pump_configs: List of pump configurations.

        Returns:
            Dictionary mapping bottle numbers to SinglePin instances.

        """
        pin_map: dict[int, SinglePin] = {}
        for bottle_num, pump_config in enumerate(pump_configs, start=1):
            pin_map[bottle_num] = self.create_pin(pump_config)
            _logger.debug(f"Created {pump_config.pin_type} pin for bottle {bottle_num} (pin {pump_config.pin})")
        return pin_map
