from __future__ import annotations

from typing import TYPE_CHECKING

from src.config.config_types import I2CExpanderConfig
from src.logger_handler import LoggerHandler
from src.machine.i2c.i2c_expander import get_i2c_device
from src.machine.interface import SinglePinController

try:
    from adafruit_bus_device.i2c_device import I2CDevice

    MODULE_AVAILABLE = True
except (ModuleNotFoundError, RuntimeError):
    MODULE_AVAILABLE = False

if TYPE_CHECKING:
    import busio

_logger = LoggerHandler("PCA9535")


class PCA9535:
    """Driver for PCA9535 16-bit I2C GPIO expander."""

    # Register addresses
    _REG_INPUT_PORT_0 = 0x00
    _REG_INPUT_PORT_1 = 0x01
    _REG_OUTPUT_PORT_0 = 0x02
    _REG_OUTPUT_PORT_1 = 0x03
    _REG_CONFIG_0 = 0x06
    _REG_CONFIG_1 = 0x07

    def __init__(self, i2c: busio.I2C, address: int = 0x20) -> None:
        self._device = I2CDevice(i2c, address)
        self._address = address
        # Cache output and config register values to allow per-pin manipulation
        self._output = [0x00, 0x00]  # Port 0, Port 1
        self._config = [0xFF, 0xFF]  # Default: all inputs

    def _write_register(self, reg: int, value: int) -> None:
        with self._device as i2c:
            i2c.write(bytes([reg, value]))

    def _read_register(self, reg: int) -> int:
        buf = bytearray(1)
        with self._device as i2c:
            i2c.write_then_readinto(bytes([reg]), buf)
        return buf[0]

    def _get_port_and_bit(self, pin: int) -> tuple[int, int]:
        """Convert pin number to port index and bit mask."""
        port = pin // 8  # 0 for pins 0-7, 1 for pins 8-15
        bit = 1 << (pin % 8)
        return port, bit

    def set_pin_mode(self, pin: int, is_output: bool) -> None:
        """Set a pin as input or output."""
        port, bit = self._get_port_and_bit(pin)
        if is_output:
            self._config[port] &= ~bit  # Clear bit = output
        else:
            self._config[port] |= bit  # Set bit = input
        reg = self._REG_CONFIG_0 if port == 0 else self._REG_CONFIG_1
        self._write_register(reg, self._config[port])

    def set_pin_value(self, pin: int, value: bool) -> None:
        """Set output value for a pin."""
        port, bit = self._get_port_and_bit(pin)
        if value:
            self._output[port] |= bit
        else:
            self._output[port] &= ~bit
        reg = self._REG_OUTPUT_PORT_0 if port == 0 else self._REG_OUTPUT_PORT_1
        self._write_register(reg, self._output[port])

    def read_pin(self, pin: int) -> bool:
        """Read input value for a pin."""
        port, bit = self._get_port_and_bit(pin)
        reg = self._REG_INPUT_PORT_0 if port == 0 else self._REG_INPUT_PORT_1
        value = self._read_register(reg)
        return bool(value & bit)


class PCA9535GPIO(SinglePinController):
    """GPIO controller for a single PCA9535 pin."""

    def __init__(self, pin: int, inverted: bool, device: PCA9535 | None) -> None:
        self.high = True
        self.low = False
        if inverted:
            self.high, self.low = self.low, self.high
        self.pin = pin
        self._device = device

    def initialize(self, is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize the PCA9535 pin."""
        if self._device is None:
            _logger.warning(f"Could not import I2C dependencies. Will not be able to control pin: PCA9535-{self.pin}")
            return

        try:
            self._device.set_pin_mode(self.pin, is_output=not is_input)
            if not is_input:
                self._device.set_pin_value(self.pin, self.low)
            _logger.debug(f"Initialized PCA9535 pin {self.pin} as {'input' if is_input else 'output'}")
        except Exception as e:
            _logger.error(f"Could not initialize PCA9535 pin {self.pin}: {e}")

    def activate(self) -> None:
        if self._device is None:
            return
        self._device.set_pin_value(self.pin, self.high)

    def close(self) -> None:
        if self._device is None:
            return
        self._device.set_pin_value(self.pin, self.low)

    def cleanup(self) -> None:
        self.close()

    def read(self) -> bool:
        if self._device is None:
            return False
        return self._device.read_pin(self.pin)


def get_pca9535(config: I2CExpanderConfig, i2c: busio.I2C | None) -> PCA9535 | None:
    """Get or create a PCA9535 device at the given address."""
    if not MODULE_AVAILABLE:
        _logger.info("PCA9535 module not available")
        return None
    return get_i2c_device(config, i2c, PCA9535, "PCA9535")
