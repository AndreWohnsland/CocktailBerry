"""Pin implementations for GPIO and I2C expanders."""

from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.i2c_expanders import MCP23017Device, PCF8574Device

_logger = LoggerHandler("PinImplementations")


class GpioPin:
    """Wrapper for GPIO pins using existing GPIO controller."""

    def __init__(self, gpio_controller: object, pin: int, inverted: bool) -> None:
        """Initialize GPIO pin wrapper.

        Args:
        ----
            gpio_controller: GPIOController instance (RaspberryGPIO or GenericGPIO)
            pin: GPIO pin number
            inverted: Whether to invert the logic

        """
        self.gpio_controller = gpio_controller
        self.pin = pin
        self.inverted = inverted
        self.initialized = False

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the GPIO pin."""
        if not self.initialized:
            self.gpio_controller.initialize()
            self.initialized = True

    def activate(self) -> None:
        """Activate the pin (set to HIGH/ON state)."""
        self.gpio_controller.activate()

    def close(self) -> None:
        """Close the pin (set to LOW/OFF state)."""
        self.gpio_controller.close()

    def cleanup(self) -> None:
        """Clean up resources associated with the pin."""
        self.gpio_controller.cleanup()

    def read(self) -> bool:
        """Read the current state of the pin.

        Returns
        -------
            bool: True if pin is HIGH, False if LOW

        Raises
        ------
            NotImplementedError: GPIO controller wrapper does not support reading

        """
        # GPIO controllers in the factory pattern don't expose read functionality
        # Reading pins should be done through the main PinController.read_pin() method
        msg = "GPIO pin reading not supported through this wrapper. Use PinController.read_pin() instead."
        raise NotImplementedError(msg)


class I2cMcp23017Pin:
    """Pin implementation for MCP23017 I2C expander."""

    def __init__(self, device: MCP23017Device, pin_number: int, inverted: bool) -> None:
        """Initialize MCP23017 pin.

        Args:
        ----
            device: MCP23017 device manager
            pin_number: Pin number on the expander (0-15)
            inverted: Whether to invert the logic

        """
        self.device = device
        self.pin_number = pin_number
        self.inverted = inverted
        self.pin = device.get_pin(pin_number)
        self.initialized = False

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the I2C pin.

        Args:
        ----
            is_input: True for input mode, False for output mode
            pull_down: Not used for I2C expanders (no internal pull-up/down)

        """
        if not self.initialized:
            if is_input:
                msg = "I2C expanders do not support input mode for relay control"
                raise NotImplementedError(msg)
            self.pin.set_direction(is_input=False, inverted=self.inverted)
            self.initialized = True

    def activate(self) -> None:
        """Activate the pin (set to HIGH/ON state)."""
        self.pin.set_value(True)

    def close(self) -> None:
        """Close the pin (set to LOW/OFF state)."""
        self.pin.set_value(False)

    def cleanup(self) -> None:
        """Clean up resources associated with the pin."""
        self.pin.cleanup()

    def read(self) -> bool:
        """Read the current state of the pin.

        Returns
        -------
            bool: True if pin is HIGH, False if LOW

        """
        return self.pin.get_value()


class I2cPcf8574Pin:
    """Pin implementation for PCF8574 I2C expander."""

    def __init__(self, device: PCF8574Device, pin_number: int, inverted: bool) -> None:
        """Initialize PCF8574 pin.

        Args:
        ----
            device: PCF8574 device manager
            pin_number: Pin number on the expander (0-7)
            inverted: Whether to invert the logic

        """
        self.device = device
        self.pin_number = pin_number
        self.inverted = inverted
        self.pin = device.get_pin(pin_number)
        self.initialized = False

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the I2C pin.

        Args:
        ----
            is_input: True for input mode, False for output mode
            pull_down: Not used for I2C expanders (no internal pull-up/down)

        """
        if not self.initialized:
            if is_input:
                msg = "I2C expanders do not support input mode for relay control"
                raise NotImplementedError(msg)
            self.pin.set_direction(is_input=False, inverted=self.inverted)
            self.initialized = True

    def activate(self) -> None:
        """Activate the pin (set to HIGH/ON state)."""
        self.pin.set_value(True)

    def close(self) -> None:
        """Close the pin (set to LOW/OFF state)."""
        self.pin.set_value(False)

    def cleanup(self) -> None:
        """Clean up resources associated with the pin."""
        self.pin.cleanup()

    def read(self) -> bool:
        """Read the current state of the pin.

        Returns
        -------
            bool: True if pin is HIGH, False if LOW

        """
        return self.pin.get_value()
