"""Tests for UnionType configuration."""

import pytest

from src.config.config_types import (
    BoolType,
    ChooseType,
    IntType,
    ListType,
    NormalLedConfig,
    StringType,
    UnionType,
    WsLedConfig,
)
from src.config.errors import ConfigError
from src.config.validators import build_number_limiter


class TestLedConfigs:
    """Test LED config classes."""

    def test_normal_led_config_to_config(self):
        """Test NormalLedConfig serialization."""
        config = NormalLedConfig(led_type="normal", pin=14, default_on=False, preparation_state="Effect")
        result = config.to_config()
        assert result == {"type": "normal", "pin": 14, "default_on": False, "preparation_state": "Effect"}

    def test_normal_led_config_from_config(self):
        """Test NormalLedConfig deserialization."""
        config_dict = {"type": "normal", "pin": 14, "default_on": True, "preparation_state": "On"}
        config = NormalLedConfig.from_config(config_dict)
        assert config.type == "normal"
        assert config.pin == 14
        assert config.default_on is True
        assert config.preparation_state == "On"

    def test_normal_led_config_defaults(self):
        """Test NormalLedConfig with defaults."""
        config = NormalLedConfig()
        assert config.type == "normal"
        assert config.pin == 14
        assert config.default_on is False
        assert config.preparation_state == "Effect"

    def test_ws_led_config_to_config(self):
        """Test WsLedConfig serialization."""
        config = WsLedConfig(led_type="ws281x", pin=18, count=24, brightness=100, number_rings=1, default_on=False, preparation_state="Effect")
        result = config.to_config()
        assert result == {
            "type": "ws281x",
            "pin": 18,
            "count": 24,
            "brightness": 100,
            "number_rings": 1,
            "default_on": False,
            "preparation_state": "Effect",
        }

    def test_ws_led_config_from_config(self):
        """Test WsLedConfig deserialization."""
        config_dict = {"type": "ws281x", "pin": 18, "count": 24, "brightness": 100, "number_rings": 1, "default_on": True, "preparation_state": "On"}
        config = WsLedConfig.from_config(config_dict)
        assert config.type == "ws281x"
        assert config.pin == 18
        assert config.count == 24
        assert config.brightness == 100
        assert config.number_rings == 1
        assert config.default_on is True
        assert config.preparation_state == "On"

    def test_ws_led_config_defaults(self):
        """Test WsLedConfig with defaults."""
        config = WsLedConfig()
        assert config.type == "ws281x"
        assert config.pin == 18
        assert config.count == 24
        assert config.brightness == 100
        assert config.number_rings == 1
        assert config.default_on is False
        assert config.preparation_state == "Effect"


class TestUnionType:
    """Test UnionType configuration type."""

    def setup_method(self):
        """Setup test fixtures."""
        self.union_type = UnionType[WsLedConfig | NormalLedConfig](
            type_field="type",
            variants={
                "normal": (
                    NormalLedConfig,
                    {
                        "type": StringType(),
                        "pin": IntType([build_number_limiter(0, 200)]),
                        "default_on": BoolType(check_name="Default On"),
                        "preparation_state": ChooseType(allowed=["Off", "On", "Effect"]),
                    },
                ),
                "ws281x": (
                    WsLedConfig,
                    {
                        "type": StringType(),
                        "pin": IntType([build_number_limiter(0, 200)]),
                        "count": IntType([build_number_limiter(1, 500)]),
                        "brightness": IntType([build_number_limiter(1, 255)]),
                        "number_rings": IntType([build_number_limiter(1, 10)]),
                        "default_on": BoolType(check_name="Default On"),
                        "preparation_state": ChooseType(allowed=["Off", "On", "Effect"]),
                    },
                ),
            },
        )

    def test_validate_normal_led(self):
        """Test validation of normal LED config."""
        config = {"type": "normal", "pin": 14, "default_on": False, "preparation_state": "Effect"}
        # Should not raise
        self.union_type.validate("test_config", config)

    def test_validate_ws_led(self):
        """Test validation of WS LED config."""
        config = {"type": "ws281x", "pin": 18, "count": 24, "brightness": 100, "number_rings": 1, "default_on": False, "preparation_state": "Effect"}
        # Should not raise
        self.union_type.validate("test_config", config)

    def test_validate_missing_type(self):
        """Test validation fails when type field is missing."""
        config = {"pin": 18, "count": 24}
        with pytest.raises(ConfigError, match="missing required 'type' field"):
            self.union_type.validate("test_config", config)

    def test_validate_invalid_type(self):
        """Test validation fails with invalid type value."""
        config = {"type": "invalid", "pin": 14, "default_on": False, "preparation_state": "Effect"}
        with pytest.raises(ConfigError, match="invalid type='invalid'"):
            self.union_type.validate("test_config", config)

    def test_validate_missing_field_for_variant(self):
        """Test validation fails when required field is missing."""
        config = {"type": "ws281x", "pin": 18}  # missing count, brightness, number_rings, default_on, preparation_state
        with pytest.raises(ConfigError, match="missing in 'test_config'"):
            self.union_type.validate("test_config", config)

    def test_from_config_normal(self):
        """Test deserialization of normal LED config."""
        config_dict = {"type": "normal", "pin": 14, "default_on": False, "preparation_state": "Effect"}
        result = self.union_type.from_config(config_dict)
        assert isinstance(result, NormalLedConfig)
        assert result.type == "normal"
        assert result.pin == 14
        assert result.default_on is False

    def test_from_config_ws(self):
        """Test deserialization of WS LED config."""
        config_dict = {"type": "ws281x", "pin": 18, "count": 24, "brightness": 100, "number_rings": 1, "default_on": False, "preparation_state": "Effect"}
        result = self.union_type.from_config(config_dict)
        assert isinstance(result, WsLedConfig)
        assert result.type == "ws281x"
        assert result.pin == 18
        assert result.count == 24

    def test_to_config_normal(self):
        """Test serialization of normal LED config."""
        config = NormalLedConfig(led_type="normal", pin=14, default_on=False, preparation_state="Effect")
        result = self.union_type.to_config(config)
        assert result == {"type": "normal", "pin": 14, "default_on": False, "preparation_state": "Effect"}

    def test_to_config_ws(self):
        """Test serialization of WS LED config."""
        config = WsLedConfig(led_type="ws281x", pin=18, count=24, brightness=100, number_rings=1, default_on=False, preparation_state="Effect")
        result = self.union_type.to_config(config)
        assert result == {
            "type": "ws281x",
            "pin": 18,
            "count": 24,
            "brightness": 100,
            "number_rings": 1,
            "default_on": False,
            "preparation_state": "Effect",
        }

    def test_validate_out_of_range_values(self):
        """Test validation fails with out-of-range values."""
        config = {"type": "ws281x", "pin": 300, "count": 24, "brightness": 100, "number_rings": 1, "default_on": False, "preparation_state": "Effect"}
        with pytest.raises(ConfigError):
            self.union_type.validate("test_config", config)



class TestConfigManagerIntegration:
    """Test ConfigManager integration with LED_CONFIG."""

    def test_led_config_in_manager(self):
        """Test that LED_CONFIG is properly configured in ConfigManager."""
        from src.config.config_manager import CONFIG

        assert "LED_CONFIG" in CONFIG.config_type
        led_config_type = CONFIG.config_type["LED_CONFIG"]
        assert isinstance(led_config_type, ListType)
        assert isinstance(led_config_type.list_type, UnionType)

    def test_get_config_includes_led_config(self):
        """Test that get_config includes LED_CONFIG."""
        from src.config.config_manager import CONFIG

        config = CONFIG.get_config()
        assert "LED_CONFIG" in config
        assert isinstance(config["LED_CONFIG"], list)
        assert len(config["LED_CONFIG"]) > 0

    def test_set_and_get_led_config(self):
        """Test setting and getting LED_CONFIG."""
        from src.config.config_manager import CONFIG

        # Set a normal LED config
        led_configs = [{"type": "normal", "pin": 14, "default_on": False, "preparation_state": "Effect"}]
        CONFIG.set_config({"LED_CONFIG": led_configs}, validate=True)
        
        # Verify it was set
        result = CONFIG.LED_CONFIG
        assert len(result) == 1
        assert isinstance(result[0], NormalLedConfig)
        assert result[0].pin == 14

    def test_set_and_get_ws_led_config(self):
        """Test setting and getting WS LED config."""
        from src.config.config_manager import CONFIG

        # Set a WS LED config
        led_configs = [{"type": "ws281x", "pin": 18, "count": 30, "brightness": 150, "number_rings": 2, "default_on": False, "preparation_state": "Effect"}]
        CONFIG.set_config({"LED_CONFIG": led_configs}, validate=True)
        
        # Verify it was set
        result = CONFIG.LED_CONFIG
        assert len(result) == 1
        assert isinstance(result[0], WsLedConfig)
        assert result[0].pin == 18
        assert result[0].count == 30
        assert result[0].brightness == 150
        assert result[0].number_rings == 2

    def test_set_mixed_led_configs(self):
        """Test setting multiple LED configs of different types."""
        from src.config.config_manager import CONFIG

        # Set mixed LED configs
        led_configs = [
            {"type": "ws281x", "pin": 18, "count": 24, "brightness": 100, "number_rings": 1, "default_on": False, "preparation_state": "Effect"},
            {"type": "normal", "pin": 14, "default_on": True, "preparation_state": "On"},
        ]
        CONFIG.set_config({"LED_CONFIG": led_configs}, validate=True)
        
        # Verify both were set
        result = CONFIG.LED_CONFIG
        assert len(result) == 2
        assert isinstance(result[0], WsLedConfig)
        assert isinstance(result[1], NormalLedConfig)
