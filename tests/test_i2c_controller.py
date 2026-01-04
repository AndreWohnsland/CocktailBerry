"""Tests for I2C relay controller."""

from unittest.mock import MagicMock, patch

import pytest

from src.machine.i2c_board import I2CController


class TestI2CController:
    """Test I2C controller functionality."""

    @pytest.fixture
    def mock_smbus(self):
        """Mock SMBus for testing."""
        with patch("src.machine.i2c_board.SMBus") as mock:
            yield mock

    @pytest.fixture
    def controller(self):
        """Create a basic I2C controller instance."""
        return I2CController(inverted=False, i2c_addresses=[0x20, 0x21], bus_number=1)

    @pytest.fixture
    def controller_inverted(self):
        """Create an inverted I2C controller instance."""
        return I2CController(inverted=True, i2c_addresses=[0x20], bus_number=1)

    def test_pin_to_device_bit(self, controller):
        """Test pin to device/bit mapping."""
        # Test first device (pins 1-8)
        assert controller._pin_to_device_bit(1) == (0, 0)
        assert controller._pin_to_device_bit(2) == (0, 1)
        assert controller._pin_to_device_bit(8) == (0, 7)

        # Test second device (pins 9-16)
        assert controller._pin_to_device_bit(9) == (1, 0)
        assert controller._pin_to_device_bit(10) == (1, 1)
        assert controller._pin_to_device_bit(16) == (1, 7)

    def test_initialize_pin_list(self, controller, mock_smbus):
        """Test pin list initialization."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus

        controller.initialize_pin_list([1, 2, 3, 9])

        # Should create bus and initialize devices to low (0x00)
        mock_smbus.assert_called_once_with(1)
        assert mock_bus.write_byte.call_count == 2  # Two devices
        mock_bus.write_byte.assert_any_call(0x20, 0x00)
        mock_bus.write_byte.assert_any_call(0x21, 0x00)

    def test_initialize_pin_list_no_smbus(self):
        """Test initialization without smbus2 installed."""
        # Create controller in dev mode (smbus not available)
        with patch("src.machine.i2c_board.DEV", True):
            controller = I2CController(inverted=False, i2c_addresses=[0x20], bus_number=1)
            # Should not raise exception
            controller.initialize_pin_list([1, 2, 3])
            assert controller.devenvironment is True

    def test_activate_single_pin(self, controller, mock_smbus):
        """Test activating a single pin."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 2])

        # Activate pin 1 (device 0, bit 0)
        controller.activate_pin_list([1])

        # Should set bit 0 to 1: 0x00 | 0x01 = 0x01
        mock_bus.write_byte.assert_called_with(0x20, 0x01)

    def test_activate_multiple_pins_same_device(self, controller, mock_smbus):
        """Test activating multiple pins on same device."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 2, 3])

        # Activate pins 1 and 3
        controller.activate_pin_list([1, 3])

        # Should set bits 0 and 2: 0x05 (binary: 00000101)
        calls = [call for call in mock_bus.write_byte.call_args_list if call[0][1] != 0x00]
        assert any(call[0][1] == 0x05 for call in calls)

    def test_activate_pins_different_devices(self, controller, mock_smbus):
        """Test activating pins on different devices."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 9])

        # Activate pin 1 (device 0x20) and pin 9 (device 0x21)
        controller.activate_pin_list([1, 9])

        # Should write to both devices
        mock_bus.write_byte.assert_any_call(0x20, 0x01)
        mock_bus.write_byte.assert_any_call(0x21, 0x01)

    def test_close_pin(self, controller, mock_smbus):
        """Test closing (deactivating) a pin."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 2])

        # Activate both pins
        controller.activate_pin_list([1, 2])
        # Should be 0x03 (binary: 00000011)
        assert controller.device_states[0x20] == 0x03

        # Close pin 1
        controller.close_pin_list([1])

        # Should clear bit 0: 0x03 & ~0x01 = 0x02
        assert controller.device_states[0x20] == 0x02
        mock_bus.write_byte.assert_called_with(0x20, 0x02)

    def test_inverted_logic(self, controller_inverted, mock_smbus):
        """Test inverted logic (active low)."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller_inverted.initialize_pin_list([1, 2])

        # Inverted: initialize should write 0xFF (all high/off)
        mock_bus.write_byte.assert_called_with(0x20, 0xFF)

        # Activate pin 1 (should clear bit 0)
        controller_inverted.activate_pin_list([1])
        # 0xFF & ~0x01 = 0xFE (binary: 11111110)
        assert controller_inverted.device_states[0x20] == 0xFE

        # Close pin 1 (should set bit 0)
        controller_inverted.close_pin_list([1])
        # 0xFE | 0x01 = 0xFF
        assert controller_inverted.device_states[0x20] == 0xFF

    def test_read_pin(self, controller, mock_smbus):
        """Test reading pin state."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 2])

        # Initially all pins should be off
        assert controller.read_pin(1) is False
        assert controller.read_pin(2) is False

        # Activate pin 1
        controller.activate_pin_list([1])
        assert controller.read_pin(1) is True
        assert controller.read_pin(2) is False

        # Activate pin 2
        controller.activate_pin_list([2])
        assert controller.read_pin(1) is True
        assert controller.read_pin(2) is True

        # Close pin 1
        controller.close_pin_list([1])
        assert controller.read_pin(1) is False
        assert controller.read_pin(2) is True

    def test_read_pin_inverted(self, controller_inverted, mock_smbus):
        """Test reading pin state with inverted logic."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller_inverted.initialize_pin_list([1])

        # Initially all pins should be off (but register is 0xFF)
        assert controller_inverted.read_pin(1) is False

        # Activate pin 1 (clear bit in register)
        controller_inverted.activate_pin_list([1])
        assert controller_inverted.read_pin(1) is True

    def test_cleanup(self, controller, mock_smbus):
        """Test cleanup turns off all relays."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 2, 9])

        # Activate some pins
        controller.activate_pin_list([1, 9])

        # Cleanup
        controller.cleanup_pin_list()

        # Should write 0x00 to all devices and close bus
        mock_bus.write_byte.assert_any_call(0x20, 0x00)
        mock_bus.write_byte.assert_any_call(0x21, 0x00)
        mock_bus.close.assert_called_once()

    def test_pin_out_of_range(self, controller, mock_smbus):
        """Test handling of pins that map to non-existent devices."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1])

        # Try to activate pin 17 (would need a 3rd device)
        # Should log warning but not crash
        controller.activate_pin_list([17])

        # Should only write to first device for pin 1 initialization
        # Pin 17 should be ignored
        assert all(call[0][0] in [0x20, 0x21] for call in mock_bus.write_byte.call_args_list)

    def test_state_preservation(self, controller, mock_smbus):
        """Test that state is preserved across operations."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 2, 3])

        # Activate pins 1 and 2
        controller.activate_pin_list([1, 2])
        state_after_12 = controller.device_states[0x20]

        # Activate pin 3 (should not affect 1 and 2)
        controller.activate_pin_list([3])
        # State should be: bits 0, 1, 2 set = 0x07
        assert controller.device_states[0x20] == 0x07

        # Close pin 2 (should not affect 1 and 3)
        controller.close_pin_list([2])
        # State should be: bits 0, 2 set = 0x05
        assert controller.device_states[0x20] == 0x05

    def test_exception_handling_during_write(self, controller, mock_smbus):
        """Test exception handling during I2C write operations."""
        mock_bus = MagicMock()
        mock_bus.write_byte.side_effect = IOError("I2C write failed")
        mock_smbus.return_value = mock_bus

        controller.initialize_pin_list([1])
        # Should not raise exception, but log error
        controller.activate_pin_list([1])
        # Should continue execution

    def test_multiple_devices_independence(self, controller, mock_smbus):
        """Test that multiple I2C devices operate independently."""
        mock_bus = MagicMock()
        mock_smbus.return_value = mock_bus
        controller.initialize_pin_list([1, 9])

        # Activate pin 1 on first device
        controller.activate_pin_list([1])
        assert controller.device_states[0x20] == 0x01
        assert controller.device_states[0x21] == 0x00

        # Activate pin 9 on second device
        controller.activate_pin_list([9])
        assert controller.device_states[0x20] == 0x01
        assert controller.device_states[0x21] == 0x01

        # Close pin 1 on first device
        controller.close_pin_list([1])
        assert controller.device_states[0x20] == 0x00
        assert controller.device_states[0x21] == 0x01  # Should remain unchanged
