"""Integration tests for LED_CONFIG in ConfigManager."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config.config_manager import ConfigManager
from src.config.config_types import NormalLedConfig, WS281xLedConfig
from src.config.errors import ConfigError


class TestLedConfigIntegration:
    """Integration tests for LED_CONFIG functionality."""

    @pytest.fixture
    def temp_config_file(self, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a temporary config file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        # Mock the CUSTOM_CONFIG_FILE path
        from src import filepath
        monkeypatch.setattr(filepath, "CUSTOM_CONFIG_FILE", temp_path)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_led_config_default_value(self) -> None:
        """Test that LED_CONFIG has correct default value."""
        cfg = ConfigManager()
        
        assert len(cfg.LED_CONFIG) == 1
        assert isinstance(cfg.LED_CONFIG[0], WS281xLedConfig)
        assert cfg.LED_CONFIG[0].led_type == "ws281x"
        assert cfg.LED_CONFIG[0].brightness == 100
        assert cfg.LED_CONFIG[0].count == 24

    def test_led_config_in_config_type(self) -> None:
        """Test that LED_CONFIG is registered in config_type."""
        cfg = ConfigManager()
        
        assert "LED_CONFIG" in cfg.config_type
        config_setting = cfg.config_type["LED_CONFIG"]
        assert config_setting is not None

    def test_get_config_includes_led_config(self) -> None:
        """Test that get_config includes LED_CONFIG."""
        cfg = ConfigManager()
        config = cfg.get_config()
        
        assert "LED_CONFIG" in config
        assert isinstance(config["LED_CONFIG"], list)
        assert len(config["LED_CONFIG"]) == 1
        assert config["LED_CONFIG"][0]["led_type"] == "ws281x"

    def test_set_config_with_normal_led(self) -> None:
        """Test setting LED_CONFIG with normal LED."""
        cfg = ConfigManager()
        
        new_config = {
            "LED_CONFIG": [
                {
                    "led_type": "normal",
                    "pins": [14, 15],
                    "brightness": 200,
                    "default_on": True,
                    "preparation_state": "On",
                }
            ]
        }
        
        cfg.set_config(new_config, validate=True)
        
        assert len(cfg.LED_CONFIG) == 1
        assert isinstance(cfg.LED_CONFIG[0], NormalLedConfig)
        assert cfg.LED_CONFIG[0].led_type == "normal"
        assert cfg.LED_CONFIG[0].pins == [14, 15]
        assert cfg.LED_CONFIG[0].brightness == 200
        assert cfg.LED_CONFIG[0].default_on is True

    def test_set_config_with_ws281x_led(self) -> None:
        """Test setting LED_CONFIG with WS281x LED."""
        cfg = ConfigManager()
        
        new_config = {
            "LED_CONFIG": [
                {
                    "led_type": "ws281x",
                    "pins": [18],
                    "brightness": 150,
                    "count": 30,
                    "number_rings": 2,
                    "default_on": False,
                    "preparation_state": "Effect",
                }
            ]
        }
        
        cfg.set_config(new_config, validate=True)
        
        assert len(cfg.LED_CONFIG) == 1
        assert isinstance(cfg.LED_CONFIG[0], WS281xLedConfig)
        assert cfg.LED_CONFIG[0].led_type == "ws281x"
        assert cfg.LED_CONFIG[0].pins == [18]
        assert cfg.LED_CONFIG[0].brightness == 150
        assert cfg.LED_CONFIG[0].count == 30
        assert cfg.LED_CONFIG[0].number_rings == 2

    def test_set_config_with_multiple_leds(self) -> None:
        """Test setting LED_CONFIG with multiple LED configurations."""
        cfg = ConfigManager()
        
        new_config = {
            "LED_CONFIG": [
                {
                    "led_type": "normal",
                    "pins": [14],
                    "brightness": 100,
                    "default_on": False,
                    "preparation_state": "On",
                },
                {
                    "led_type": "ws281x",
                    "pins": [18],
                    "brightness": 150,
                    "count": 30,
                    "number_rings": 1,
                    "default_on": True,
                    "preparation_state": "Effect",
                },
            ]
        }
        
        cfg.set_config(new_config, validate=True)
        
        assert len(cfg.LED_CONFIG) == 2
        assert isinstance(cfg.LED_CONFIG[0], NormalLedConfig)
        assert isinstance(cfg.LED_CONFIG[1], WS281xLedConfig)

    def test_set_config_validates_led_type(self) -> None:
        """Test that invalid LED type is rejected."""
        cfg = ConfigManager()
        
        new_config = {
            "LED_CONFIG": [
                {
                    "led_type": "invalid_type",
                    "pins": [14],
                    "brightness": 100,
                    "default_on": False,
                    "preparation_state": "On",
                }
            ]
        }
        
        with pytest.raises(ConfigError, match="invalid led_type"):
            cfg.set_config(new_config, validate=True)

    def test_set_config_validates_missing_fields(self) -> None:
        """Test that missing required fields are rejected."""
        cfg = ConfigManager()
        
        new_config = {
            "LED_CONFIG": [
                {
                    "led_type": "normal",
                    "pins": [14],
                    # Missing brightness, default_on, preparation_state
                }
            ]
        }
        
        with pytest.raises(ConfigError, match="is missing"):
            cfg.set_config(new_config, validate=True)

    def test_sync_and_load_led_config(self, temp_config_file: Path) -> None:
        """Test syncing LED_CONFIG to file and loading it back."""
        cfg = ConfigManager()
        
        # Set custom LED config
        new_config = {
            "LED_CONFIG": [
                {
                    "led_type": "ws281x",
                    "pins": [12],
                    "brightness": 255,
                    "count": 50,
                    "number_rings": 3,
                    "default_on": True,
                    "preparation_state": "Effect",
                }
            ]
        }
        cfg.set_config(new_config, validate=True)
        
        # Sync to file
        cfg.sync_config_to_file()
        
        # Create new manager and load config
        cfg2 = ConfigManager()
        cfg2.read_local_config(validate=True)
        
        # Verify loaded config matches
        assert len(cfg2.LED_CONFIG) == 1
        assert isinstance(cfg2.LED_CONFIG[0], WS281xLedConfig)
        assert cfg2.LED_CONFIG[0].led_type == "ws281x"
        assert cfg2.LED_CONFIG[0].pins == [12]
        assert cfg2.LED_CONFIG[0].brightness == 255
        assert cfg2.LED_CONFIG[0].count == 50
        assert cfg2.LED_CONFIG[0].number_rings == 3

    def test_get_config_with_ui_information_led_config(self) -> None:
        """Test that get_config_with_ui_information includes LED_CONFIG metadata."""
        cfg = ConfigManager()
        config = cfg.get_config_with_ui_information()
        
        assert "LED_CONFIG" in config
        led_config_info = config["LED_CONFIG"]
        
        # Check that dynamic config metadata is included
        assert "discriminator_field" in led_config_info
        assert led_config_info["discriminator_field"] == "led_type"
        assert "type_options" in led_config_info
        assert set(led_config_info["type_options"]) == {"normal", "ws281x"}
        assert "type_schemas" in led_config_info
        
        # Check normal schema
        assert "normal" in led_config_info["type_schemas"]
        normal_schema = led_config_info["type_schemas"]["normal"]
        assert "led_type" in normal_schema
        assert "pins" in normal_schema
        assert "brightness" in normal_schema
        assert "default_on" in normal_schema
        assert "preparation_state" in normal_schema
        
        # Check ws281x schema
        assert "ws281x" in led_config_info["type_schemas"]
        ws281x_schema = led_config_info["type_schemas"]["ws281x"]
        assert "count" in ws281x_schema
        assert "number_rings" in ws281x_schema


class TestLegacyLedConfigMigration:
    """Tests for migrating legacy LED configuration to new LED_CONFIG."""

    def test_migrate_ws281x_led_config_logic(self) -> None:
        """Test the migration logic for WS281x LED configuration."""
        cfg = ConfigManager()
        
        # Simulate having legacy config loaded
        cfg.LED_PINS = [18, 19]
        cfg.LED_BRIGHTNESS = 200
        cfg.LED_COUNT = 50
        cfg.LED_NUMBER_RINGS = 3
        cfg.LED_DEFAULT_ON = True
        cfg.LED_PREPARATION_STATE = "On"
        cfg.LED_IS_WS = True
        cfg.LED_CONFIG = []  # Empty to trigger migration
        
        # Call migration with empty dict (no LED_CONFIG in loaded config)
        cfg._migrate_legacy_led_config({})
        
        # Verify migration
        assert len(cfg.LED_CONFIG) == 1
        assert isinstance(cfg.LED_CONFIG[0], WS281xLedConfig)
        assert cfg.LED_CONFIG[0].led_type == "ws281x"
        assert cfg.LED_CONFIG[0].pins == [18, 19]
        assert cfg.LED_CONFIG[0].brightness == 200
        assert cfg.LED_CONFIG[0].count == 50
        assert cfg.LED_CONFIG[0].number_rings == 3
        assert cfg.LED_CONFIG[0].default_on is True
        assert cfg.LED_CONFIG[0].preparation_state == "On"

    def test_migrate_normal_led_config_logic(self) -> None:
        """Test the migration logic for normal LED configuration."""
        cfg = ConfigManager()
        
        # Simulate having legacy config loaded
        cfg.LED_PINS = [14, 15, 16]
        cfg.LED_BRIGHTNESS = 150
        cfg.LED_DEFAULT_ON = False
        cfg.LED_PREPARATION_STATE = "Effect"
        cfg.LED_IS_WS = False
        cfg.LED_CONFIG = []  # Empty to trigger migration
        
        # Call migration with empty dict (no LED_CONFIG in loaded config)
        cfg._migrate_legacy_led_config({})
        
        # Verify migration
        assert len(cfg.LED_CONFIG) == 1
        assert isinstance(cfg.LED_CONFIG[0], NormalLedConfig)
        assert cfg.LED_CONFIG[0].led_type == "normal"
        assert cfg.LED_CONFIG[0].pins == [14, 15, 16]
        assert cfg.LED_CONFIG[0].brightness == 150
        assert cfg.LED_CONFIG[0].default_on is False
        assert cfg.LED_CONFIG[0].preparation_state == "Effect"

    def test_no_migration_when_led_config_in_loaded_config(self) -> None:
        """Test that migration doesn't occur when LED_CONFIG exists in loaded config."""
        cfg = ConfigManager()
        
        # Simulate having legacy config
        cfg.LED_PINS = [18]
        cfg.LED_BRIGHTNESS = 100
        cfg.LED_IS_WS = True
        
        # But also have new config
        existing_config = WS281xLedConfig(
            led_type="ws281x",
            pins=[12],
            brightness=255,
            count=30,
            number_rings=1,
            default_on=False,
            preparation_state="Effect",
        )
        cfg.LED_CONFIG = [existing_config]
        
        # Call migration with LED_CONFIG in loaded dict
        cfg._migrate_legacy_led_config({"LED_CONFIG": [existing_config.to_config()]})
        
        # Verify migration didn't happen - still has the existing config
        assert len(cfg.LED_CONFIG) == 1
        assert cfg.LED_CONFIG[0].pins == [12]  # From existing config, not legacy
        assert cfg.LED_CONFIG[0].brightness == 255  # From existing config

    def test_no_migration_when_no_legacy_changes(self) -> None:
        """Test that migration doesn't occur when legacy config has all default values."""
        cfg = ConfigManager()
        
        # All default values
        cfg.LED_PINS = []
        cfg.LED_BRIGHTNESS = 100
        cfg.LED_COUNT = 24
        cfg.LED_NUMBER_RINGS = 1
        cfg.LED_DEFAULT_ON = False
        cfg.LED_PREPARATION_STATE = "Effect"
        cfg.LED_IS_WS = True
        cfg.LED_CONFIG = []  # Empty
        
        # Call migration
        cfg._migrate_legacy_led_config({})
        
        # Verify no migration happened (LED_CONFIG stays empty)
        assert len(cfg.LED_CONFIG) == 0
