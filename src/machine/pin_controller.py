"""Module to create the according GPIO controller for the appropriate Board."""

from __future__ import annotations

from typing import Self

from src import SupportedPinControlType
from src.config.config_manager import CONFIG as cfg
from src.config.config_types import MCP23017ConfigClass, PCF8574ConfigClass, PinId
from src.logger_handler import LoggerHandler
from src.machine.generic_board import GenericGPIO
from src.machine.i2c_expander import MCP23017GPIO, PCF8574GPIO, get_i2c, get_mcp23017, get_pcf8574
from src.machine.interface import SinglePinController
from src.machine.raspberry import RaspberryGPIO, Rpi5GPIO, is_rpi, is_rpi5

_logger = LoggerHandler("PinControllerFactory")


class SinglePinControllerFactory:
    def __init__(self, mcp_config: MCP23017ConfigClass, pcf_config: PCF8574ConfigClass) -> None:
        self._i2c = None
        if mcp_config.enabled or pcf_config.enabled:
            self._i2c = get_i2c()
        self.mcp23017 = get_mcp23017(mcp_config, self._i2c)
        self.pcf8574 = get_pcf8574(pcf_config, self._i2c)

    def generate_single_pin_controller(
        self,
        pin: int,
        pin_type: SupportedPinControlType,
        invert_override: bool | None = None,
    ) -> SinglePinController:
        """Return the appropriate GPIO.

        Option to specific invert one GPIO relative to general setting.
        """
        gpio_inverted = cfg.MAKER_PINS_INVERTED if invert_override is None else invert_override
        match pin_type:
            case "MCP23017":
                return MCP23017GPIO(
                    pin,
                    cfg.MCP23017_CONFIG.inverted if invert_override is None else invert_override,
                    self.mcp23017,
                )
            case "PCF8574":
                return PCF8574GPIO(
                    pin,
                    cfg.PCF8574_CONFIG.inverted if invert_override is None else invert_override,
                    self.pcf8574,
                )
            case "GPIO":
                if is_rpi5():
                    return Rpi5GPIO(pin, gpio_inverted)
                if is_rpi():
                    return RaspberryGPIO(pin, gpio_inverted)
                return GenericGPIO(pin, gpio_inverted)
            case _:
                return GenericGPIO(pin, gpio_inverted)


class PinController:
    """Use PinControllerAdapter to create per-pin controllers, allowing mixed pin types (GPIO, I2C expanders)."""

    _instance: Self | None = None

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._factory = SinglePinControllerFactory(cfg.MCP23017_CONFIG, cfg.PCF8574_CONFIG)
        self._pins: dict[PinId, SinglePinController] = {}
        self._initialized = True

    # INIT operations
    def initialize_pin(
        self,
        pin_id: PinId,
        is_input: bool = False,
        pull_down: bool = True,
        invert_override: bool | None = None,
    ) -> SinglePinController:
        """Create and initialize a SinglePinController for a pin."""
        controller = self._factory.generate_single_pin_controller(pin_id.pin, pin_id.pin_type, invert_override)
        controller.initialize(is_input, pull_down)
        self._pins[pin_id] = controller
        return controller

    def initialize_pin_list(
        self,
        pin_list: list[PinId],
        is_input: bool = False,
        pull_down: bool = True,
    ) -> list[SinglePinController]:
        """Create and initialize a SinglePinController for each pin."""
        return [self.initialize_pin(pin_id, is_input, pull_down) for pin_id in pin_list]

    # ON operations
    def activate_pin(self, pin_id: PinId) -> None:
        """Activate a pin via its SinglePinController."""
        if pin := self._pins.get(pin_id):
            pin.activate()
        else:
            _logger.warning(f"Attempted to activate uninitialized pin: {pin_id}")

    def activate_pin_list(self, pin_list: list[PinId]) -> None:
        """Activate each pin via its SinglePinController."""
        for pin_id in pin_list:
            self.activate_pin(pin_id)

    def read_pin(self, pin_id: PinId) -> bool:
        """Read the state of a pin."""
        if pin := self._pins.get(pin_id):
            return pin.read()
        _logger.warning(f"Attempted to read uninitialized pin: {pin}")
        return False

    # OFF operations
    def close_pin(self, pin_id: PinId) -> None:
        """Close a pin via its SinglePinController."""
        if pin := self._pins.get(pin_id):
            pin.close()
        else:
            _logger.info(f"Attempted to close uninitialized pin: {pin_id}, might be already cleaned up.")

    def close_pin_list(self, pin_list: list[PinId]) -> None:
        """Close each pin via its SinglePinController."""
        for pin_id in pin_list:
            self.close_pin(pin_id)

    # CLEANUP operations
    def cleanup_pin(self, pin_id: PinId) -> None:
        """Clean up a single pin."""
        if pin := self._pins.get(pin_id):
            _logger.info(f"<c> Cleaning up pin: {pin_id}")
            pin.cleanup()
            del self._pins[pin_id]
        else:
            _logger.warning(f"Attempted to clean up uninitialized pin: {pin_id}")

    def cleanup_pin_list(self, pin_list: list[PinId] | None = None) -> None:
        """Clean up pins. If no list given, clean up all."""
        if pin_list is None:
            _logger.info("<c> Cleaning up all initialized pins")
            for controller in self._pins.values():
                controller.cleanup()
            self._pins.clear()
        else:
            for pin_id in pin_list:
                self.cleanup_pin(pin_id)
