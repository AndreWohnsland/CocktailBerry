"""I2C-based relay controller for controlling pumps via I2C protocol.

This module provides I2C relay control support for devices like PCF8574 or MCP23017.
Each I2C device can control 8 bits (relays), and multiple devices can be chained.
Pump mapping: Pump 1 -> Bit 1, Pump 2 -> Bit 2, etc.
For multiple I2C devices: Device 1 (pumps 1-8), Device 2 (pumps 9-16), etc.
"""

from __future__ import annotations

from src.logger_handler import LoggerHandler
from src.machine.interface import PinController

_logger = LoggerHandler("I2CController")

try:
    # pylint: disable=import-error
    from smbus2 import SMBus  # type: ignore

    DEV = False
except ModuleNotFoundError:
    DEV = True


class I2CController(PinController):
    """Controller class to control relays via I2C protocol.

    This controller maps logical pin numbers to I2C device addresses and bit positions.
    Pin numbers 1-8 map to first I2C device, 9-16 to second device, etc.
    Each bit on the I2C device controls one relay.
    """

    def __init__(self, inverted: bool, i2c_addresses: list[int], bus_number: int = 1) -> None:
        """Initialize I2C controller.

        Args:
        ----
            inverted: If True, inverts the signal (on=low, off=high)
            i2c_addresses: List of I2C device addresses (e.g., [0x20, 0x21] for two PCF8574)
            bus_number: I2C bus number (default 1 for Raspberry Pi)

        """
        super().__init__()
        self.inverted = inverted
        self.i2c_addresses = i2c_addresses
        self.bus_number = bus_number
        self.devenvironment = DEV
        self.low: int = 0
        self.high: int = 0xFF
        if inverted:
            self.low, self.high = self.high, self.low
        # Track current state of each I2C device (8 bits per device)
        self.device_states: dict[int, int] = dict.fromkeys(i2c_addresses, self.low)
        self.bus: SMBus | None = None
        self.dev_displayed = False

    def initialize_pin_list(self, pin_list: list[int], is_input: bool = False, pull_down: bool = True) -> None:
        """Set up the given pin list.

        Args:
        ----
            pin_list: List of logical pin numbers (1-based)
            is_input: Not supported for I2C relays, must be False
            pull_down: Not used for I2C relays

        """
        if not self.dev_displayed:
            _logger.info(f"<i> Devenvironment on the I2C Control module is {'on' if self.devenvironment else 'off'}")
            self.dev_displayed = True
            if self.devenvironment:
                _logger.warning("Could not import smbus2. Will not be able to control I2C relays")
                _logger.warning("Try to install smbus2: pip install smbus2")

        if self.devenvironment:
            return

        if is_input:
            _logger.error("I2C relay controller does not support input pins")
            return

        try:
            self.bus = SMBus(self.bus_number)
            # Initialize all I2C devices to off state
            for addr in self.i2c_addresses:
                self.bus.write_byte(addr, self.device_states[addr])
            _logger.info(f"<i> Initialized I2C devices at addresses: {[hex(addr) for addr in self.i2c_addresses]}")
        except FileNotFoundError as e:
            self.devenvironment = True
            _logger.log_exception(e)
            _logger.error("I2C device not found. Make sure I2C is enabled: sudo raspi-config")
        except (IOError, OSError) as e:
            self.devenvironment = True
            _logger.log_exception(e)
            _logger.error("I2C communication error. Check device addresses and wiring")
        except PermissionError as e:
            self.devenvironment = True
            _logger.log_exception(e)
            _logger.error("Permission denied. Run as root or add user to i2c group: sudo usermod -a -G i2c $USER")

    def activate_pin_list(self, pin_list: list[int]) -> None:
        """Activates the given pin list (turns on relays).

        Args:
        ----
            pin_list: List of logical pin numbers (1-based)

        """
        if self.devenvironment or self.bus is None:
            return

        for pin in pin_list:
            device_idx, bit_pos = self._pin_to_device_bit(pin)
            if device_idx >= len(self.i2c_addresses):
                _logger.warning(f"Pin {pin} maps to device index {device_idx} which doesn't exist")
                continue

            addr = self.i2c_addresses[device_idx]
            # Set the bit to activate the relay
            if self.inverted:
                self.device_states[addr] &= ~(1 << bit_pos)
            else:
                self.device_states[addr] |= (1 << bit_pos)

            try:
                self.bus.write_byte(addr, self.device_states[addr])
            except (IOError, OSError) as e:
                _logger.error(f"Failed to activate pin {pin} on I2C device {hex(addr)}: {e}")

    def close_pin_list(self, pin_list: list[int]) -> None:
        """Close (deactivate) the given pin_list (turns off relays).

        Args:
        ----
            pin_list: List of logical pin numbers (1-based)

        """
        if self.devenvironment or self.bus is None:
            return

        for pin in pin_list:
            device_idx, bit_pos = self._pin_to_device_bit(pin)
            if device_idx >= len(self.i2c_addresses):
                _logger.warning(f"Pin {pin} maps to device index {device_idx} which doesn't exist")
                continue

            addr = self.i2c_addresses[device_idx]
            # Clear the bit to deactivate the relay
            if self.inverted:
                self.device_states[addr] |= (1 << bit_pos)
            else:
                self.device_states[addr] &= ~(1 << bit_pos)

            try:
                self.bus.write_byte(addr, self.device_states[addr])
            except (IOError, OSError) as e:
                _logger.error(f"Failed to close pin {pin} on I2C device {hex(addr)}: {e}")

    def cleanup_pin_list(self, pin_list: list[int] | None = None) -> None:
        """Clean up I2C resources.

        Args:
        ----
            pin_list: Optional list of pins to cleanup (if None, cleanup all)

        """
        if self.devenvironment or self.bus is None:
            return

        try:
            # Turn off all relays before cleanup
            for addr in self.i2c_addresses:
                try:
                    self.bus.write_byte(addr, self.low)
                    self.device_states[addr] = self.low
                except (IOError, OSError) as e:
                    _logger.error(f"Error turning off device {hex(addr)} during cleanup: {e}")
            self.bus.close()
            self.bus = None
        except Exception as e:
            _logger.error(f"Error during I2C cleanup: {e}")

    def read_pin(self, pin: int) -> bool:
        """Return the state of the given pin.

        Args:
        ----
            pin: Logical pin number (1-based)

        Returns:
        -------
            True if pin is active (relay on), False otherwise

        """
        if self.devenvironment or self.bus is None:
            return False

        device_idx, bit_pos = self._pin_to_device_bit(pin)
        if device_idx >= len(self.i2c_addresses):
            return False

        addr = self.i2c_addresses[device_idx]
        state = self.device_states[addr]

        if self.inverted:
            return not bool(state & (1 << bit_pos))
        return bool(state & (1 << bit_pos))

    def _pin_to_device_bit(self, pin: int) -> tuple[int, int]:
        """Convert logical pin number to device index and bit position.

        Args:
        ----
            pin: Logical pin number (1-based, e.g., 1-16 for two 8-bit devices)

        Returns:
        -------
            Tuple of (device_index, bit_position)
            Example: pin 1 -> (0, 0), pin 9 -> (1, 0), pin 10 -> (1, 1)

        """
        # Pin numbering is 1-based, but we need 0-based for calculations
        zero_based_pin = pin - 1
        device_idx = zero_based_pin // 8  # Which I2C device (0, 1, 2, ...)
        bit_pos = zero_based_pin % 8  # Which bit on that device (0-7)
        return device_idx, bit_pos
