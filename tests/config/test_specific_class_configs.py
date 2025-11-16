import pytest

from src.config.config_types import NormalLedConfig, PumpConfig, WS281xLedConfig


class TestPumpConfig:
    """Tests for PumpConfig class."""

    def test_initialization(self) -> None:
        """Test PumpConfig initialization."""
        pump = PumpConfig(pin=14, volume_flow=30.0, tube_volume=5)
        assert pump.pin == 14
        assert pump.volume_flow == pytest.approx(30.0)
        assert pump.tube_volume == 5

    def test_to_config(self) -> None:
        """Test PumpConfig serialization to dict."""
        pump = PumpConfig(pin=14, volume_flow=30.0, tube_volume=5)
        result = pump.to_config()
        assert result["pin"] == 14
        assert result["volume_flow"] == pytest.approx(30.0)
        assert result["tube_volume"] == 5
        assert isinstance(result, dict)

    def test_from_config(self) -> None:
        """Test PumpConfig deserialization from dict."""
        config_dict = {"pin": 14, "volume_flow": 30.0, "tube_volume": 5}
        pump = PumpConfig.from_config(config_dict)
        assert isinstance(pump, PumpConfig)
        assert pump.pin == 14
        assert pump.volume_flow == pytest.approx(30.0)
        assert pump.tube_volume == 5

    def test_round_trip_serialization(self) -> None:
        """Test that serialization and deserialization are inverses.

        This edge case ensures config data integrity during save/load cycles.
        """
        original = PumpConfig(pin=7, volume_flow=25.5, tube_volume=8)
        config_dict = original.to_config()
        restored = PumpConfig.from_config(config_dict)
        assert original.pin == restored.pin
        assert original.volume_flow == pytest.approx(restored.volume_flow)
        assert original.tube_volume == restored.tube_volume
        assert original.tube_volume == restored.tube_volume


class TestNormalLedConfig:
    """Tests for NormalLedConfig class."""

    def test_initialization(self) -> None:
        """Test NormalLedConfig initialization."""
        led = NormalLedConfig(
            pin=17,
            brightness=255,
            default_on=True,
            preparation_state="On",
        )
        assert led.pin == 17
        assert led.brightness == 255
        assert led.default_on is True
        assert led.preparation_state == "On"

    def test_to_config(self) -> None:
        """Test NormalLedConfig serialization to dict."""
        led = NormalLedConfig(
            pin=17,
            brightness=200,
            default_on=False,
            preparation_state="Off",
        )
        result = led.to_config()
        assert result["pin"] == 17
        assert result["brightness"] == 200
        assert result["default_on"] is False
        assert result["preparation_state"] == "Off"
        assert isinstance(result, dict)

    def test_from_config(self) -> None:
        """Test NormalLedConfig deserialization from dict."""
        config_dict = {
            "pin": 17,
            "brightness": 200,
            "default_on": False,
            "preparation_state": "Off",
        }
        led = NormalLedConfig.from_config(config_dict)
        assert isinstance(led, NormalLedConfig)
        assert led.pin == 17
        assert led.brightness == 200
        assert led.default_on is False
        assert led.preparation_state == "Off"

    def test_round_trip_serialization(self) -> None:
        """Test that serialization and deserialization are inverses.

        This edge case ensures config data integrity during save/load cycles.
        """
        original = NormalLedConfig(
            pin=27,
            brightness=150,
            default_on=True,
            preparation_state="Effect",
        )
        config_dict = original.to_config()
        restored = NormalLedConfig.from_config(config_dict)
        assert original.pin == restored.pin
        assert original.brightness == restored.brightness
        assert original.default_on == restored.default_on
        assert original.preparation_state == restored.preparation_state


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
