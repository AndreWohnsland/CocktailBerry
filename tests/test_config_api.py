"""Tests for API config endpoints."""

import pytest

from src.config.config_manager import CONFIG
from src.config.config_types import NormalLedConfig, WsLedConfig


class TestConfigAPI:
    """Test config API functionality."""

    def test_get_config_includes_led_config(self):
        """Test that get_config returns LED_CONFIG."""
        config = CONFIG.get_config()
        assert "LED_CONFIG" in config
        assert isinstance(config["LED_CONFIG"], list)

    def test_get_config_with_ui_information(self):
        """Test that get_config_with_ui_information includes variant metadata."""
        config = CONFIG.get_config_with_ui_information()
        assert "LED_CONFIG" in config
        led_config = config["LED_CONFIG"]
        
        # Check that it has the UnionType metadata
        assert "type_field" in led_config
        assert led_config["type_field"] == "type"
        assert "variants" in led_config
        assert "normal" in led_config["variants"]
        assert "ws281x" in led_config["variants"]
        
        # Check that variants have field metadata
        normal_variant = led_config["variants"]["normal"]
        assert "pins" in normal_variant
        
        ws_variant = led_config["variants"]["ws281x"]
        assert "pin" in ws_variant
        assert "count" in ws_variant
        assert "brightness" in ws_variant
        assert "number_rings" in ws_variant

    def test_set_led_config_via_dict(self):
        """Test setting LED_CONFIG through set_config method."""
        # Save original config
        original = CONFIG.LED_CONFIG
        
        try:
            # Set new config
            new_config = {
                "LED_CONFIG": [
                    {"type": "normal", "pins": [14, 15, 18]},
                    {"type": "ws281x", "pin": 18, "count": 30, "brightness": 150, "number_rings": 2},
                ]
            }
            CONFIG.set_config(new_config, validate=True)
            
            # Verify it was set
            assert len(CONFIG.LED_CONFIG) == 2
            assert isinstance(CONFIG.LED_CONFIG[0], NormalLedConfig)
            assert CONFIG.LED_CONFIG[0].pins == [14, 15, 18]
            assert isinstance(CONFIG.LED_CONFIG[1], WsLedConfig)
            assert CONFIG.LED_CONFIG[1].count == 30
            
        finally:
            # Restore original
            CONFIG.LED_CONFIG = original

    def test_round_trip_serialization(self):
        """Test that config can be serialized and deserialized."""
        # Save original config
        original = CONFIG.LED_CONFIG
        
        try:
            # Set initial config
            initial_config = {
                "LED_CONFIG": [
                    {"type": "ws281x", "pin": 18, "count": 24, "brightness": 100, "number_rings": 1},
                ]
            }
            CONFIG.set_config(initial_config, validate=True)
            
            # Get config and set it again (round trip)
            config_dict = CONFIG.get_config()
            CONFIG.set_config({"LED_CONFIG": config_dict["LED_CONFIG"]}, validate=True)
            
            # Verify it's still the same
            assert len(CONFIG.LED_CONFIG) == 1
            assert isinstance(CONFIG.LED_CONFIG[0], WsLedConfig)
            assert CONFIG.LED_CONFIG[0].pin == 18
            assert CONFIG.LED_CONFIG[0].count == 24
            
        finally:
            # Restore original
            CONFIG.LED_CONFIG = original

    def test_validation_rejects_invalid_type(self):
        """Test that validation rejects invalid type values."""
        from src.config.errors import ConfigError
        
        # Save original config
        original = CONFIG.LED_CONFIG
        
        try:
            invalid_config = {
                "LED_CONFIG": [
                    {"type": "invalid_type", "pins": [14, 15]},
                ]
            }
            
            with pytest.raises(ConfigError, match="invalid type='invalid_type'"):
                CONFIG.set_config(invalid_config, validate=True)
                
        finally:
            # Restore original
            CONFIG.LED_CONFIG = original

    def test_validation_rejects_missing_fields(self):
        """Test that validation rejects configs with missing required fields."""
        from src.config.errors import ConfigError
        
        # Save original config
        original = CONFIG.LED_CONFIG
        
        try:
            # WS config missing required fields
            invalid_config = {
                "LED_CONFIG": [
                    {"type": "ws281x", "pin": 18},  # missing count, brightness, number_rings
                ]
            }
            
            with pytest.raises(ConfigError, match="missing in"):
                CONFIG.set_config(invalid_config, validate=True)
                
        finally:
            # Restore original
            CONFIG.LED_CONFIG = original
