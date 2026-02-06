"""Tests for hybrid pin controller and I2C support."""

# Setup path relative to this file
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.config.config_types import PumpConfig
from src.machine.hybrid_controller import HybridPinController, PinDescriptor
from src.machine.pin_types import PinType


class TestPumpConfig:
    """Test PumpConfig with new fields."""

    def test_pump_config_gpio(self):
        """Test PumpConfig with GPIO type."""
        config = PumpConfig(pin=14, volume_flow=30.0, tube_volume=0)
        assert config.pin == 14
        assert config.volume_flow == 30.0
        assert config.tube_volume == 0
        assert config.pin_type == "GPIO"
        assert config.i2c_address is None

    def test_pump_config_i2c(self):
        """Test PumpConfig with I2C type."""
        config = PumpConfig(pin=0, volume_flow=30.0, tube_volume=0, pin_type="MCP23017", i2c_address=0x20)
        assert config.pin == 0
        assert config.volume_flow == 30.0
        assert config.tube_volume == 0
        assert config.pin_type == "MCP23017"
        assert config.i2c_address == 0x20

    def test_pump_config_to_config(self):
        """Test PumpConfig serialization."""
        config = PumpConfig(pin=0, volume_flow=30.0, tube_volume=5, pin_type="PCF8574", i2c_address=0x21)
        config_dict = config.to_config()
        assert config_dict["pin"] == 0
        assert config_dict["volume_flow"] == 30.0
        assert config_dict["tube_volume"] == 5
        assert config_dict["pin_type"] == "PCF8574"
        assert config_dict["i2c_address"] == 0x21

    def test_pump_config_from_config(self):
        """Test PumpConfig deserialization."""
        config_dict = {"pin": 1, "volume_flow": 25.0, "tube_volume": 3, "pin_type": "MCP23017", "i2c_address": 0x22}
        config = PumpConfig.from_config(config_dict)
        assert config.pin == 1
        assert config.volume_flow == 25.0
        assert config.tube_volume == 3
        assert config.pin_type == "MCP23017"
        assert config.i2c_address == 0x22


class TestPinTypes:
    """Test PinType enumeration."""

    def test_pin_types_exist(self):
        """Test that all expected pin types exist."""
        assert PinType.GPIO.value == "GPIO"
        assert PinType.MCP23017.value == "MCP23017"
        assert PinType.PCF8574.value == "PCF8574"

    def test_pin_type_from_string(self):
        """Test creating PinType from string."""
        assert PinType("GPIO") == PinType.GPIO
        assert PinType("MCP23017") == PinType.MCP23017
        assert PinType("PCF8574") == PinType.PCF8574


class TestPinDescriptor:
    """Test PinDescriptor."""

    def test_gpio_descriptor(self):
        """Test GPIO pin descriptor."""
        desc = PinDescriptor(pin_id=1, pin_type=PinType.GPIO, pin_number=14)
        assert desc.pin_id == 1
        assert desc.pin_type == PinType.GPIO
        assert desc.pin_number == 14
        assert desc.i2c_address is None

    def test_i2c_descriptor(self):
        """Test I2C pin descriptor."""
        desc = PinDescriptor(pin_id=2, pin_type=PinType.MCP23017, pin_number=0, i2c_address=0x20)
        assert desc.pin_id == 2
        assert desc.pin_type == PinType.MCP23017
        assert desc.pin_number == 0
        assert desc.i2c_address == 0x20


class TestHybridPinController:
    """Test HybridPinController."""

    @patch("src.machine.hybrid_controller.GPIOFactory")
    def test_initialization(self, mock_gpio_factory):
        """Test HybridPinController initialization."""
        controller = HybridPinController(inverted=True, gpio_factory=mock_gpio_factory, board_type="RPI")
        assert controller.inverted is True
        assert controller.gpio_factory == mock_gpio_factory
        assert controller.board_type == "RPI"
        assert len(controller.pins) == 0
        assert len(controller.pin_descriptors) == 0

    @patch("src.machine.hybrid_controller.GPIOFactory")
    def test_register_gpio_pin(self, mock_gpio_factory):
        """Test registering a GPIO pin."""
        controller = HybridPinController(inverted=False, gpio_factory=mock_gpio_factory, board_type="RPI")
        pump_config = PumpConfig(pin=14, volume_flow=30.0, tube_volume=0)
        controller.register_pin_from_config(pin_id=1, pump_config=pump_config)

        assert 1 in controller.pin_descriptors
        desc = controller.pin_descriptors[1]
        assert desc.pin_type == PinType.GPIO
        assert desc.pin_number == 14

    @patch("src.machine.hybrid_controller.GPIOFactory")
    def test_register_i2c_pin(self, mock_gpio_factory):
        """Test registering an I2C pin."""
        controller = HybridPinController(inverted=False, gpio_factory=mock_gpio_factory, board_type="RPI")
        pump_config = PumpConfig(pin=0, volume_flow=30.0, tube_volume=0, pin_type="MCP23017", i2c_address=0x20)
        controller.register_pin_from_config(pin_id=2, pump_config=pump_config)

        assert 2 in controller.pin_descriptors
        desc = controller.pin_descriptors[2]
        assert desc.pin_type == PinType.MCP23017
        assert desc.pin_number == 0
        assert desc.i2c_address == 0x20

    @patch("src.machine.hybrid_controller.GPIOFactory")
    @patch("src.machine.hybrid_controller.GpioPin")
    def test_initialize_gpio_pin(self, mock_gpio_pin_class, mock_gpio_factory):
        """Test initializing a GPIO pin."""
        # Setup mocks
        mock_gpio_controller = Mock()
        mock_gpio_factory.generate_gpio = Mock(return_value=mock_gpio_controller)
        mock_gpio_pin = Mock()
        mock_gpio_pin_class.return_value = mock_gpio_pin

        controller = HybridPinController(inverted=False, gpio_factory=mock_gpio_factory, board_type="RPI")
        pump_config = PumpConfig(pin=14, volume_flow=30.0, tube_volume=0)
        controller.register_pin_from_config(pin_id=1, pump_config=pump_config)

        # Initialize pin
        controller.initialize_pin_list([1], is_input=False, pull_down=True)

        # Verify pin was initialized
        assert 1 in controller.pins
        mock_gpio_pin.initialize.assert_called_once_with(is_input=False, pull_down=True)

    @patch("src.machine.hybrid_controller.GPIOFactory")
    @patch("src.machine.hybrid_controller.GpioPin")
    def test_activate_pin(self, mock_gpio_pin_class, mock_gpio_factory):
        """Test activating a pin."""
        # Setup mocks
        mock_gpio_controller = Mock()
        mock_gpio_factory.generate_gpio = Mock(return_value=mock_gpio_controller)
        mock_gpio_pin = Mock()
        mock_gpio_pin_class.return_value = mock_gpio_pin

        controller = HybridPinController(inverted=False, gpio_factory=mock_gpio_factory, board_type="RPI")
        pump_config = PumpConfig(pin=14, volume_flow=30.0, tube_volume=0)
        controller.register_pin_from_config(pin_id=1, pump_config=pump_config)
        controller.initialize_pin_list([1])

        # Activate pin
        controller.activate_pin_list([1])

        # Verify
        mock_gpio_pin.activate.assert_called_once()

    @patch("src.machine.hybrid_controller.GPIOFactory")
    @patch("src.machine.hybrid_controller.GpioPin")
    def test_close_pin(self, mock_gpio_pin_class, mock_gpio_factory):
        """Test closing a pin."""
        # Setup mocks
        mock_gpio_controller = Mock()
        mock_gpio_factory.generate_gpio = Mock(return_value=mock_gpio_controller)
        mock_gpio_pin = Mock()
        mock_gpio_pin_class.return_value = mock_gpio_pin

        controller = HybridPinController(inverted=False, gpio_factory=mock_gpio_factory, board_type="RPI")
        pump_config = PumpConfig(pin=14, volume_flow=30.0, tube_volume=0)
        controller.register_pin_from_config(pin_id=1, pump_config=pump_config)
        controller.initialize_pin_list([1])

        # Close pin
        controller.close_pin_list([1])

        # Verify
        mock_gpio_pin.close.assert_called_once()

    @patch("src.machine.hybrid_controller.GPIOFactory")
    @patch("src.machine.hybrid_controller.GpioPin")
    def test_cleanup_pin(self, mock_gpio_pin_class, mock_gpio_factory):
        """Test cleaning up a pin."""
        # Setup mocks
        mock_gpio_controller = Mock()
        mock_gpio_factory.generate_gpio = Mock(return_value=mock_gpio_controller)
        mock_gpio_pin = Mock()
        mock_gpio_pin_class.return_value = mock_gpio_pin

        controller = HybridPinController(inverted=False, gpio_factory=mock_gpio_factory, board_type="RPI")
        pump_config = PumpConfig(pin=14, volume_flow=30.0, tube_volume=0)
        controller.register_pin_from_config(pin_id=1, pump_config=pump_config)
        controller.initialize_pin_list([1])

        # Cleanup pin
        controller.cleanup_pin_list([1])

        # Verify
        mock_gpio_pin.cleanup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
