"""I2C GPIO expander implementations for MCP23017 and PCF8574.

This module provides SinglePin implementations for I2C GPIO expanders,
enabling control of pumps via MCP23017 (16 pins) and PCF8574 (8 pins).
Uses Adafruit CircuitPython libraries for I2C communication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from src.logger_handler import LoggerHandler
from src.machine.interface import SinglePin

_logger = LoggerHandler("I2CExpander")

# Try importing Adafruit libraries for MCP23017
# These are only available on Linux (Raspberry Pi)
try:
    import board  # ty: ignore[unresolved-import]
    import busio  # ty: ignore[unresolved-import]
    from adafruit_mcp230xx.mcp23017 import MCP23017  # ty: ignore[unresolved-import]
    from digitalio import Direction, Pull  # ty: ignore[unresolved-import]

    MCP23017_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    MCP23017_AVAILABLE = False
    MCP23017 = None

# Try importing Adafruit libraries for PCF8574
# These are only available on Linux (Raspberry Pi)
try:
    import board  # ty: ignore[unresolved-import]
    import busio  # ty: ignore[unresolved-import]
    from adafruit_pcf8574 import PCF8574  # ty: ignore[unresolved-import]
    from digitalio import Direction, Pull  # ty: ignore[unresolved-import]

    PCF8574_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    PCF8574_AVAILABLE = False
    PCF8574 = None

if TYPE_CHECKING:
    from adafruit_mcp230xx.mcp23017 import MCP23017  # ty: ignore[unresolved-import]
    from adafruit_pcf8574 import PCF8574  # ty: ignore[unresolved-import]


class I2CDeviceRegistry:
    """Singleton registry for I2C expander devices to avoid re-initialization.

    Manages the I2C bus and device instances, ensuring only one instance
    per I2C address is created.
    """

    _instance = None
    _i2c: Any | None = None
    _mcp23017_devices: ClassVar[dict[int, MCP23017]] = {}
    _pcf8574_devices: ClassVar[dict[int, PCF8574]] = {}

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._mcp23017_devices = {}
            cls._pcf8574_devices = {}
        return cls._instance

    def get_i2c(self) -> Any | None:
        """Get or create the I2C bus.

        Returns:
            The I2C bus instance, or None if initialization fails.

        """
        if self._i2c is None:
            if not (MCP23017_AVAILABLE or PCF8574_AVAILABLE):
                _logger.warning("No I2C libraries available. Install adafruit-blinka and device libraries.")
                return None
            try:
                self._i2c = busio.I2C(board.SCL, board.SDA)
            except Exception as e:
                _logger.error(f"Could not initialize I2C bus: {e}")
                return None
        return self._i2c

    def get_mcp23017(self, address: int) -> MCP23017 | None:
        """Get or create an MCP23017 device at the given address.

        Args:
            address: I2C address of the device (0x20-0x27).

        Returns:
            The MCP23017 device instance, or None if initialization fails.

        """
        if not MCP23017_AVAILABLE or MCP23017 is None:
            _logger.warning("MCP23017 library not available. Install adafruit-circuitpython-mcp230xx.")
            return None
        if address not in self._mcp23017_devices:
            i2c = self.get_i2c()
            if i2c is None:
                return None
            try:
                self._mcp23017_devices[address] = MCP23017(i2c, address=address)
                _logger.info(f"Initialized MCP23017 at address 0x{address:02x}")
            except Exception as e:
                _logger.error(f"Could not initialize MCP23017 at 0x{address:02x}: {e}")
                return None
        return self._mcp23017_devices[address]

    def get_pcf8574(self, address: int) -> PCF8574 | None:
        """Get or create a PCF8574 device at the given address.

        Args:
            address: I2C address of the device (0x20-0x27).

        Returns:
            The PCF8574 device instance, or None if initialization fails.

        """
        if not PCF8574_AVAILABLE or PCF8574 is None:
            _logger.warning("PCF8574 library not available. Install adafruit-circuitpython-pcf8574.")
            return None
        if address not in self._pcf8574_devices:
            i2c = self.get_i2c()
            if i2c is None:
                return None
            try:
                self._pcf8574_devices[address] = PCF8574(i2c, address=address)
                _logger.info(f"Initialized PCF8574 at address 0x{address:02x}")
            except Exception as e:
                _logger.error(f"Could not initialize PCF8574 at 0x{address:02x}: {e}")
                return None
        return self._pcf8574_devices[address]


class MCP23017Pin(SinglePin):
    """SinglePin implementation for MCP23017 GPIO expander.

    The MCP23017 provides 16 GPIO pins (0-15) accessible via I2C.
    """

    def __init__(self, pin: int, address: int, inverted: bool = False) -> None:
        """Initialize MCP23017 pin.

        Args:
            pin: Pin number on the expander (0-15).
            address: I2C address of the device (0x20-0x27).
            inverted: Whether to invert the pin logic.

        """
        self.pin = pin
        self.address = address
        self.inverted = inverted
        self._gpio_pin: Any | None = None
        self._registry = I2CDeviceRegistry()
        self._device: MCP23017 | None = None

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the MCP23017 pin."""
        self._device = self._registry.get_mcp23017(self.address)
        if self._device is None:
            _logger.warning(f"MCP23017 not available for pin {self.pin}")
            return

        try:
            self._gpio_pin = self._device.get_pin(self.pin)
            if is_input:
                self._gpio_pin.direction = Direction.INPUT
                self._gpio_pin.pull = Pull.DOWN if pull_down else Pull.UP
            else:
                self._gpio_pin.direction = Direction.OUTPUT
                # Set initial value (low or high depending on inversion)
                self._gpio_pin.value = self.inverted
            _logger.debug(f"Initialized MCP23017 pin {self.pin} as {'input' if is_input else 'output'}")
        except Exception as e:
            _logger.error(f"Could not initialize MCP23017 pin {self.pin}: {e}")

    def activate(self) -> None:
        """Set the pin high (or low if inverted)."""
        if self._gpio_pin is not None:
            self._gpio_pin.value = not self.inverted

    def close(self) -> None:
        """Set the pin low (or high if inverted)."""
        if self._gpio_pin is not None:
            self._gpio_pin.value = self.inverted

    def cleanup(self) -> None:
        """Cleanup - set to safe state."""
        self.close()

    def read(self) -> bool:
        """Read the pin value."""
        if self._gpio_pin is not None:
            return self._gpio_pin.value
        return False


class PCF8574Pin(SinglePin):
    """SinglePin implementation for PCF8574 GPIO expander.

    The PCF8574 provides 8 GPIO pins (0-7) accessible via I2C.
    Note: PCF8574 has only internal pull-ups, no pull-down option.
    """

    def __init__(self, pin: int, address: int, inverted: bool = False) -> None:
        """Initialize PCF8574 pin.

        Args:
            pin: Pin number on the expander (0-7).
            address: I2C address of the device (0x20-0x27).
            inverted: Whether to invert the pin logic.

        """
        self.pin = pin
        self.address = address
        self.inverted = inverted
        self._gpio_pin: Any | None = None
        self._registry = I2CDeviceRegistry()
        self._device: PCF8574 | None = None

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the PCF8574 pin.

        Note: PCF8574 only supports internal pull-ups, pull_down parameter is ignored.
        """
        self._device = self._registry.get_pcf8574(self.address)
        if self._device is None:
            _logger.warning(f"PCF8574 not available for pin {self.pin}")
            return

        try:
            self._gpio_pin = self._device.get_pin(self.pin)
            if is_input:
                self._gpio_pin.direction = Direction.INPUT
                # PCF8574 has internal pull-ups only, pull_down is ignored
            else:
                self._gpio_pin.direction = Direction.OUTPUT
                # Set initial value (low or high depending on inversion)
                self._gpio_pin.value = self.inverted
            _logger.debug(f"Initialized PCF8574 pin {self.pin} as {'input' if is_input else 'output'}")
        except Exception as e:
            _logger.error(f"Could not initialize PCF8574 pin {self.pin}: {e}")

    def activate(self) -> None:
        """Set the pin high (or low if inverted)."""
        if self._gpio_pin is not None:
            self._gpio_pin.value = not self.inverted

    def close(self) -> None:
        """Set the pin low (or high if inverted)."""
        if self._gpio_pin is not None:
            self._gpio_pin.value = self.inverted

    def cleanup(self) -> None:
        """Cleanup - set to safe state."""
        self.close()

    def read(self) -> bool:
        """Read the pin value."""
        if self._gpio_pin is not None:
            return self._gpio_pin.value
        return False
