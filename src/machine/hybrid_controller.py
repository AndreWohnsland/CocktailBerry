"""Hybrid pin controller supporting GPIO and I2C expanders."""

from __future__ import annotations

from src.config.config_types import PumpConfig
from src.logger_handler import LoggerHandler
from src.machine.gpio_factory import GPIOFactory
from src.machine.i2c_expanders import MCP23017Device, PCF8574Device
from src.machine.interface import PinController
from src.machine.pin_implementations import GpioPin, I2cMcp23017Pin, I2cPcf8574Pin
from src.machine.pin_types import PinType

_logger = LoggerHandler("HybridPinController")


class PinDescriptor:
    """Descriptor for a pin (GPIO or I2C)."""

    def __init__(
        self,
        pin_id: int,
        pin_type: PinType,
        pin_number: int,
        i2c_address: int | None = None,
    ) -> None:
        """Initialize pin descriptor.

        Args:
        ----
            pin_id: Unique identifier for this pin (from config)
            pin_type: Type of pin (GPIO, MCP23017, PCF8574)
            pin_number: Pin number (GPIO pin or I2C expander pin number)
            i2c_address: I2C address (required for I2C pins)

        """
        self.pin_id = pin_id
        self.pin_type = pin_type
        self.pin_number = pin_number
        self.i2c_address = i2c_address


class HybridPinController(PinController):
    """Controller that manages both GPIO and I2C expander pins."""

    def __init__(self, inverted: bool, gpio_factory: GPIOFactory, board_type: str = "RPI") -> None:
        """Initialize hybrid controller.

        Args:
        ----
            inverted: Global inverted flag for GPIO pins
            gpio_factory: Factory for creating GPIO controllers
            board_type: Board type ("RPI" or "GENERIC")

        """
        super().__init__()
        self.inverted = inverted
        self.gpio_factory = gpio_factory
        self.board_type = board_type

        # Storage for pin implementations
        self.pins: dict[int, GpioPin | I2cMcp23017Pin | I2cPcf8574Pin] = {}
        self.pin_descriptors: dict[int, PinDescriptor] = {}

        # I2C device managers (keyed by address)
        self.mcp23017_devices: dict[int, MCP23017Device] = {}
        self.pcf8574_devices: dict[int, PCF8574Device] = {}

        _logger.info("Hybrid pin controller initialized")

    def register_pin_from_config(self, pin_id: int, pump_config: PumpConfig) -> None:
        """Register a pin from pump configuration.

        Args:
        ----
            pin_id: Unique identifier for this pin (bottle number/index)
            pump_config: Pump configuration object

        """
        pin_type = PinType(pump_config.pin_type)
        pin_number = pump_config.pin

        # For I2C, pin_number is the pin index on the expander (0-15 for MCP, 0-7 for PCF)
        # For GPIO, pin_number is the GPIO pin number
        descriptor = PinDescriptor(
            pin_id=pin_id,
            pin_type=pin_type,
            pin_number=pin_number,
            i2c_address=pump_config.i2c_address,
        )
        self.pin_descriptors[pin_id] = descriptor
        _logger.debug(
            f"Registered pin {pin_id}: type={pin_type.value}, "
            f"pin={pin_number}, i2c_addr={pump_config.i2c_address}"
        )

    def initialize_pin_list(self, pin_list: list[int], is_input: bool = False, pull_down: bool = True) -> None:
        """Initialize all registered pins.

        Args:
        ----
            pin_list: List of pin IDs to initialize
            is_input: True for input mode, False for output mode
            pull_down: True for pull-down, False for pull-up (only for GPIO)

        """
        for pin_id in pin_list:
            descriptor = self.pin_descriptors.get(pin_id)
            if descriptor is None:
                _logger.warning(f"Pin {pin_id} not registered, skipping initialization")
                continue

            try:
                pin_impl = self._create_pin_implementation(descriptor)
                pin_impl.initialize(is_input=is_input, pull_down=pull_down)
                self.pins[pin_id] = pin_impl
                _logger.debug(f"Initialized pin {pin_id} ({descriptor.pin_type.value})")
            except Exception as e:
                _logger.log_exception(e)
                _logger.error(f"Failed to initialize pin {pin_id}: {e}")

    def _create_pin_implementation(
        self, descriptor: PinDescriptor
    ) -> GpioPin | I2cMcp23017Pin | I2cPcf8574Pin:
        """Create the appropriate pin implementation based on pin type.

        Args:
        ----
            descriptor: Pin descriptor

        Returns:
        -------
            Pin implementation

        """
        if descriptor.pin_type == PinType.GPIO:
            # Create GPIO pin using factory
            gpio_controller = self.gpio_factory.generate_gpio(
                inverted=False,  # Factory handles inversion internally
                pin=descriptor.pin_number,
                board=self.board_type,
            )
            return GpioPin(gpio_controller, descriptor.pin_number, self.inverted)

        if descriptor.pin_type == PinType.MCP23017:
            # Get or create MCP23017 device
            if descriptor.i2c_address is None:
                msg = f"I2C address required for MCP23017 pin {descriptor.pin_id}"
                raise ValueError(msg)

            if descriptor.i2c_address not in self.mcp23017_devices:
                self.mcp23017_devices[descriptor.i2c_address] = MCP23017Device(descriptor.i2c_address)

            device = self.mcp23017_devices[descriptor.i2c_address]
            return I2cMcp23017Pin(device, descriptor.pin_number, self.inverted)

        if descriptor.pin_type == PinType.PCF8574:
            # Get or create PCF8574 device
            if descriptor.i2c_address is None:
                msg = f"I2C address required for PCF8574 pin {descriptor.pin_id}"
                raise ValueError(msg)

            if descriptor.i2c_address not in self.pcf8574_devices:
                self.pcf8574_devices[descriptor.i2c_address] = PCF8574Device(descriptor.i2c_address)

            device = self.pcf8574_devices[descriptor.i2c_address]
            return I2cPcf8574Pin(device, descriptor.pin_number, self.inverted)

        msg = f"Unsupported pin type: {descriptor.pin_type}"
        raise ValueError(msg)

    def activate_pin_list(self, pin_list: list[int]) -> None:
        """Activate (turn on) the specified pins.

        Args:
        ----
            pin_list: List of pin IDs to activate

        """
        for pin_id in pin_list:
            pin = self.pins.get(pin_id)
            if pin is None:
                _logger.warning(f"Pin {pin_id} not initialized, skipping activation")
                continue

            try:
                pin.activate()
            except Exception as e:
                _logger.log_exception(e)
                _logger.error(f"Failed to activate pin {pin_id}: {e}")

    def close_pin_list(self, pin_list: list[int]) -> None:
        """Close (turn off) the specified pins.

        Args:
        ----
            pin_list: List of pin IDs to close

        """
        for pin_id in pin_list:
            pin = self.pins.get(pin_id)
            if pin is None:
                _logger.warning(f"Pin {pin_id} not initialized, skipping close")
                continue

            try:
                pin.close()
            except Exception as e:
                _logger.log_exception(e)
                _logger.error(f"Failed to close pin {pin_id}: {e}")

    def cleanup_pin_list(self, pin_list: list[int] | None = None) -> None:
        """Clean up pins and I2C devices.

        Args:
        ----
            pin_list: List of pin IDs to clean up, or None for all

        """
        pins_to_cleanup = pin_list if pin_list is not None else list(self.pins.keys())

        for pin_id in pins_to_cleanup:
            pin = self.pins.get(pin_id)
            if pin is not None:
                try:
                    pin.cleanup()
                except Exception as e:
                    _logger.warning(f"Error cleaning up pin {pin_id}: {e}")

        # Clean up I2C devices
        for device in self.mcp23017_devices.values():
            try:
                device.cleanup()
            except Exception as e:
                _logger.warning(f"Error cleaning up MCP23017 device: {e}")

        for device in self.pcf8574_devices.values():
            try:
                device.cleanup()
            except Exception as e:
                _logger.warning(f"Error cleaning up PCF8574 device: {e}")

        if pin_list is None:
            self.pins.clear()
            self.mcp23017_devices.clear()
            self.pcf8574_devices.clear()

    def read_pin(self, pin: int) -> bool:
        """Read the state of a pin.

        Args:
        ----
            pin: Pin ID to read

        Returns:
        -------
            bool: True if pin is HIGH, False if LOW

        """
        pin_impl = self.pins.get(pin)
        if pin_impl is None:
            _logger.warning(f"Pin {pin} not initialized, returning False")
            return False

        try:
            return pin_impl.read()
        except Exception as e:
            _logger.log_exception(e)
            _logger.error(f"Failed to read pin {pin}: {e}")
            return False
