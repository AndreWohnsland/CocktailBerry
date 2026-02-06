"""I2C expander device managers for MCP23017 and PCF8574."""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol

from src.logger_handler import LoggerHandler

_logger = LoggerHandler("I2cExpander")

try:
    import board
    import busio
    from adafruit_mcp230xx.mcp23017 import MCP23017
    from adafruit_pcf8574 import PCF8574
    from digitalio import Direction

    I2C_AVAILABLE = True
except (ImportError, NotImplementedError):
    I2C_AVAILABLE = False
    _logger.warning("Adafruit CircuitPython libraries not available. I2C functionality will be disabled.")


class I2cExpanderDevice(Protocol):
    """Protocol for I2C expander devices."""

    @abstractmethod
    def get_pin(self, pin_number: int) -> I2cExpanderPin:
        """Get a pin object for the specified pin number.

        Args:
        ----
            pin_number: Pin number on the expander (0-indexed)

        Returns:
        -------
            I2cExpanderPin: Pin object

        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up the I2C device."""
        raise NotImplementedError


class I2cExpanderPin(Protocol):
    """Protocol for I2C expander pins."""

    @abstractmethod
    def set_direction(self, is_input: bool) -> None:
        """Set pin direction.

        Args:
        ----
            is_input: True for input, False for output

        """
        raise NotImplementedError

    @abstractmethod
    def set_value(self, value: bool) -> None:
        """Set pin value.

        Args:
        ----
            value: True for HIGH, False for LOW

        """
        raise NotImplementedError

    @abstractmethod
    def get_value(self) -> bool:
        """Get pin value.

        Returns
        -------
            bool: True if HIGH, False if LOW

        """
        raise NotImplementedError


class MCP23017Device:
    """Manager for MCP23017 I2C GPIO expander (16 pins)."""

    def __init__(self, i2c_address: int = 0x20, bus_number: int = 1) -> None:
        """Initialize MCP23017 device.

        Args:
        ----
            i2c_address: I2C address of the device (default 0x20)
            bus_number: I2C bus number (default 1)

        """
        self.i2c_address = i2c_address
        self.bus_number = bus_number
        self.device = None
        self.pins: dict[int, MCP23017Pin] = {}
        self.i2c_unavailable = not I2C_AVAILABLE

        if not self.i2c_unavailable:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.device = MCP23017(i2c, address=i2c_address)
                _logger.info(f"MCP23017 initialized at address 0x{i2c_address:02X}")
            except Exception as e:
                self.i2c_unavailable = True
                _logger.log_exception(e)
                _logger.warning(f"Could not initialize MCP23017 at 0x{i2c_address:02X}")

    def get_pin(self, pin_number: int) -> MCP23017Pin:
        """Get or create a pin object for the specified pin number.

        Args:
        ----
            pin_number: Pin number (0-15)

        Returns:
        -------
            MCP23017Pin: Pin object

        """
        if pin_number not in self.pins:
            self.pins[pin_number] = MCP23017Pin(self, pin_number)
        return self.pins[pin_number]

    def cleanup(self) -> None:
        """Clean up all pins."""
        for pin in self.pins.values():
            pin.cleanup()
        self.pins.clear()


class MCP23017Pin:
    """Individual pin on MCP23017 expander."""

    def __init__(self, device: MCP23017Device, pin_number: int) -> None:
        """Initialize pin.

        Args:
        ----
            device: Parent MCP23017 device
            pin_number: Pin number (0-15)

        """
        self.device = device
        self.pin_number = pin_number
        self.pin = None
        self.inverted = False

        if not device.i2c_unavailable and device.device is not None:
            self.pin = device.device.get_pin(pin_number)

    def set_direction(self, is_input: bool, inverted: bool = False) -> None:
        """Set pin direction and inversion.

        Args:
        ----
            is_input: True for input, False for output
            inverted: True to invert logic levels

        """
        self.inverted = inverted
        if self.pin is not None:
            self.pin.direction = Direction.INPUT if is_input else Direction.OUTPUT
            if not is_input:
                # Set initial value to LOW (or HIGH if inverted)
                self.pin.value = inverted

    def set_value(self, value: bool) -> None:
        """Set pin value.

        Args:
        ----
            value: True for HIGH, False for LOW (before inversion)

        """
        if self.pin is not None:
            actual_value = not value if self.inverted else value
            self.pin.value = actual_value

    def get_value(self) -> bool:
        """Get pin value.

        Returns
        -------
            bool: True if HIGH, False if LOW (after inversion)

        """
        if self.pin is not None:
            value = self.pin.value
            return not value if self.inverted else value
        return False

    def cleanup(self) -> None:
        """Clean up the pin (set to safe state)."""
        if self.pin is not None:
            try:
                self.pin.direction = Direction.INPUT
            except Exception as e:
                _logger.warning(f"Error cleaning up MCP23017 pin {self.pin_number}: {e}")


class PCF8574Device:
    """Manager for PCF8574 I2C GPIO expander (8 pins)."""

    def __init__(self, i2c_address: int = 0x20, bus_number: int = 1) -> None:
        """Initialize PCF8574 device.

        Args:
        ----
            i2c_address: I2C address of the device (default 0x20)
            bus_number: I2C bus number (default 1)

        """
        self.i2c_address = i2c_address
        self.bus_number = bus_number
        self.device = None
        self.pins: dict[int, PCF8574Pin] = {}
        self.i2c_unavailable = not I2C_AVAILABLE

        if not self.i2c_unavailable:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.device = PCF8574(i2c, address=i2c_address)
                _logger.info(f"PCF8574 initialized at address 0x{i2c_address:02X}")
            except Exception as e:
                self.i2c_unavailable = True
                _logger.log_exception(e)
                _logger.warning(f"Could not initialize PCF8574 at 0x{i2c_address:02X}")

    def get_pin(self, pin_number: int) -> PCF8574Pin:
        """Get or create a pin object for the specified pin number.

        Args:
        ----
            pin_number: Pin number (0-7)

        Returns:
        -------
            PCF8574Pin: Pin object

        """
        if pin_number not in self.pins:
            self.pins[pin_number] = PCF8574Pin(self, pin_number)
        return self.pins[pin_number]

    def cleanup(self) -> None:
        """Clean up all pins."""
        for pin in self.pins.values():
            pin.cleanup()
        self.pins.clear()


class PCF8574Pin:
    """Individual pin on PCF8574 expander."""

    def __init__(self, device: PCF8574Device, pin_number: int) -> None:
        """Initialize pin.

        Args:
        ----
            device: Parent PCF8574 device
            pin_number: Pin number (0-7)

        """
        self.device = device
        self.pin_number = pin_number
        self.pin = None
        self.inverted = False

        if not device.i2c_unavailable and device.device is not None:
            self.pin = device.device.get_pin(pin_number)

    def set_direction(self, is_input: bool, inverted: bool = False) -> None:
        """Set pin direction and inversion.

        Args:
        ----
            is_input: True for input, False for output
            inverted: True to invert logic levels

        """
        self.inverted = inverted
        if self.pin is not None:
            # PCF8574 pins default to INPUT, set to OUTPUT by writing
            if is_input:
                self.pin.switch_to_input()
            else:
                self.pin.switch_to_output(value=inverted)

    def set_value(self, value: bool) -> None:
        """Set pin value.

        Args:
        ----
            value: True for HIGH, False for LOW (before inversion)

        """
        if self.pin is not None:
            actual_value = not value if self.inverted else value
            self.pin.value = actual_value

    def get_value(self) -> bool:
        """Get pin value.

        Returns
        -------
            bool: True if HIGH, False if LOW (after inversion)

        """
        if self.pin is not None:
            value = self.pin.value
            return not value if self.inverted else value
        return False

    def cleanup(self) -> None:
        """Clean up the pin (set to safe state)."""
        if self.pin is not None:
            try:
                self.pin.switch_to_input()
            except Exception as e:
                _logger.warning(f"Error cleaning up PCF8574 pin {self.pin_number}: {e}")
