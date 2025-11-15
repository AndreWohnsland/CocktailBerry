import pytest

from src.config.config_types import PumpConfig


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
