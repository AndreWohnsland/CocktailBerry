from src.config.config_types import NormalGPIOLedConfig, NormalI2CLedConfig, NormalLedConfig, WS281xLedConfig

# DC pump (de)serialization is covered in `tests/config/test_discriminated_config.py`
# (TestBasePumpConfig and TestDiscriminatedDictType — round-trip and isinstance checks).
# No need to duplicate that coverage here.


class TestNormalLedConfig:
    """Tests for the Normal LED config family (GPIO + I2C subclasses)."""

    def test_gpio_routes_through_gpio_with_default_board(self) -> None:
        led = NormalGPIOLedConfig(pin=17, default_on=True, preparation_state="On")
        assert isinstance(led, NormalLedConfig)
        assert led.pin == 17
        assert led.default_on is True
        assert led.preparation_state == "On"
        # GPIO routing is encoded by the class — there are no pin_type/board_number attributes.
        assert not hasattr(led, "pin_type")
        assert not hasattr(led, "board_number")
        assert led.pin_id.pin_type == "GPIO"
        assert led.pin_id.board_number == 1

    def test_gpio_to_config_omits_pin_type_and_board(self) -> None:
        led = NormalGPIOLedConfig(pin=17, default_on=False, preparation_state="Off")
        result = led.to_config()
        assert result["pin"] == 17
        assert result["default_on"] is False
        assert result["preparation_state"] == "Off"
        assert "pin_type" not in result
        assert "board_number" not in result

    def test_gpio_round_trip(self) -> None:
        original = NormalGPIOLedConfig(pin=27, default_on=True, preparation_state="Effect")
        restored = NormalGPIOLedConfig.from_config(original.to_config())
        assert isinstance(restored, NormalGPIOLedConfig)
        assert restored.pin == original.pin
        assert restored.default_on == original.default_on
        assert restored.preparation_state == original.preparation_state

    def test_i2c_carries_expander_and_board(self) -> None:
        led = NormalI2CLedConfig(
            pin=5, default_on=False, preparation_state="Effect", pin_type="PCF8574", board_number=2
        )
        assert isinstance(led, NormalLedConfig)
        assert led.pin_type == "PCF8574"
        assert led.board_number == 2
        assert led.pin_id.pin_type == "PCF8574"
        assert led.pin_id.board_number == 2

    def test_i2c_round_trip(self) -> None:
        original = NormalI2CLedConfig(
            pin=5, default_on=True, preparation_state="On", pin_type="MCP23017", board_number=3
        )
        serialized = original.to_config()
        assert serialized["pin_type"] == "MCP23017"
        assert serialized["board_number"] == 3
        restored = NormalI2CLedConfig.from_config(serialized)
        assert isinstance(restored, NormalI2CLedConfig)
        assert restored.pin == original.pin
        assert restored.pin_type == original.pin_type
        assert restored.board_number == original.board_number


class TestWS281xLedConfig:
    """Tests for WS281xLedConfig class."""

    def test_initialization(self) -> None:
        """Test WS281xLedConfig initialization."""
        led = WS281xLedConfig(
            pin=12,
            brightness=255,
            count=30,
            number_rings=1,
            default_on=True,
            preparation_state="On",
        )
        assert led.pin == 12
        assert led.brightness == 255
        assert led.count == 30
        assert led.number_rings == 1
        assert led.default_on is True
        assert led.preparation_state == "On"

    def test_to_config(self) -> None:
        """Test WS281xLedConfig serialization to dict."""
        led = WS281xLedConfig(
            pin=12,
            brightness=200,
            count=60,
            number_rings=2,
            default_on=False,
            preparation_state="Off",
        )
        result = led.to_config()
        assert result["pin"] == 12
        assert result["brightness"] == 200
        assert result["count"] == 60
        assert result["number_rings"] == 2
        assert result["default_on"] is False
        assert result["preparation_state"] == "Off"
        assert isinstance(result, dict)

    def test_from_config(self) -> None:
        """Test WS281xLedConfig deserialization from dict."""
        config_dict = {
            "pin": 12,
            "brightness": 180,
            "count": 45,
            "number_rings": 3,
            "default_on": True,
            "preparation_state": "Effect",
        }
        led = WS281xLedConfig.from_config(config_dict)
        assert isinstance(led, WS281xLedConfig)
        assert led.pin == 12
        assert led.brightness == 180
        assert led.count == 45
        assert led.number_rings == 3
        assert led.default_on is True
        assert led.preparation_state == "Effect"

    def test_round_trip_serialization(self) -> None:
        """Test that serialization and deserialization are inverses.

        This edge case ensures config data integrity during save/load cycles.
        """
        original = WS281xLedConfig(
            pin=13,
            brightness=220,
            count=120,
            number_rings=4,
            default_on=False,
            preparation_state="Effect",
        )
        config_dict = original.to_config()
        restored = WS281xLedConfig.from_config(config_dict)
        assert original.pin == restored.pin
        assert original.brightness == restored.brightness
        assert original.count == restored.count
        assert original.number_rings == restored.number_rings
        assert original.default_on == restored.default_on
        assert original.preparation_state == restored.preparation_state
