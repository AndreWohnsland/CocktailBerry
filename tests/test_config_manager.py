"""Tests for ConfigManager class.

This module tests ConfigManager methods for reading, writing, and managing configuration.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from src.config.config_manager import ConfigManager
from src.config.config_types import IntType, PumpConfig, StringType
from src.config.errors import ConfigError


class TestConfigManagerGetConfig:
    """Tests for ConfigManager.get_config() method."""

    def test_get_config_returns_dict(self) -> None:
        """Test that get_config returns a dictionary."""
        config = ConfigManager()
        result = config.get_config()
        assert isinstance(result, dict)

    def test_get_config_contains_expected_keys(self) -> None:
        """Test that get_config includes all configured attributes."""
        config = ConfigManager()
        result = config.get_config()
        # Check some known config keys
        assert "UI_DEVENVIRONMENT" in result
        assert "MAKER_NAME" in result
        assert "PUMP_CONFIG" in result

    def test_get_config_serializes_values_correctly(self) -> None:
        """Test that get_config properly serializes different types."""
        config = ConfigManager()
        result = config.get_config()
        # Bool should stay bool
        assert isinstance(result["UI_DEVENVIRONMENT"], bool)
        # Int should stay int
        assert isinstance(result["UI_WIDTH"], int)
        # String should stay string
        assert isinstance(result["MAKER_NAME"], str)
        # List should stay list
        assert isinstance(result["PUMP_CONFIG"], list)

    def test_get_config_serializes_pump_config(self) -> None:
        """Test that PUMP_CONFIG is properly serialized to list of dicts."""
        config = ConfigManager()
        result = config.get_config()
        pump_configs = result["PUMP_CONFIG"]
        assert isinstance(pump_configs, list)
        if pump_configs:
            first_pump = pump_configs[0]
            assert isinstance(first_pump, dict)
            assert "pin" in first_pump
            assert "volume_flow" in first_pump
            assert "tube_volume" in first_pump


class TestConfigManagerSetConfig:
    """Tests for ConfigManager.set_config() method."""

    def test_set_config_updates_values(self) -> None:
        """Test that set_config updates config values."""
        config = ConfigManager()
        config.set_config({"UI_WIDTH": 1024}, validate=True)
        assert config.UI_WIDTH == 1024

    def test_set_config_with_validation_rejects_invalid(self) -> None:
        """Test that set_config with validation=True rejects invalid values."""
        config = ConfigManager()
        with pytest.raises(ConfigError):
            config.set_config({"UI_WIDTH": "not_an_int"}, validate=True)

    def test_set_config_without_validation_ignores_errors(self) -> None:
        """Test that set_config with validation=False ignores errors."""
        config = ConfigManager()
        original_width = config.UI_WIDTH
        # This should not raise, but also shouldn't update the value
        config.set_config({"UI_WIDTH": "not_an_int"}, validate=False)
        # Value should remain unchanged
        assert config.UI_WIDTH == original_width

    def test_set_config_ignores_unknown_keys(self) -> None:
        """Test that set_config ignores unknown config keys.
        
        This handles backward compatibility with old config files.
        """
        config = ConfigManager()
        # Should not raise for unknown keys
        config.set_config({"UNKNOWN_CONFIG_KEY": "value"}, validate=True)

    def test_set_config_handles_list_types(self) -> None:
        """Test that set_config properly handles list configurations."""
        config = ConfigManager()
        new_volumes = [200, 300, 400]
        config.set_config({"MAKER_PREPARE_VOLUME": new_volumes}, validate=True)
        assert config.MAKER_PREPARE_VOLUME == new_volumes

    def test_set_config_validates_list_items(self) -> None:
        """Test that set_config validates individual list items."""
        config = ConfigManager()
        # List with invalid item should fail validation
        with pytest.raises(ConfigError):
            config.set_config({"MAKER_PREPARE_VOLUME": [100, "invalid"]}, validate=True)

    def test_set_config_processes_non_list_before_list(self) -> None:
        """Test that non-list configs are processed before list configs.
        
        This is important because list lengths might depend on other config values.
        """
        config = ConfigManager()
        # Set both a simple value and a list that might depend on it
        config.set_config(
            {"MAKER_NUMBER_BOTTLES": 5, "MAKER_PREPARE_VOLUME": [150, 250]}, validate=True
        )
        assert config.MAKER_NUMBER_BOTTLES == 5
        assert config.MAKER_PREPARE_VOLUME == [150, 250]


class TestConfigManagerReadLocalConfig:
    """Tests for ConfigManager.read_local_config() method."""

    def test_read_local_config_handles_missing_file(self, tmp_path: Path) -> None:
        """Test that read_local_config doesn't fail when file is missing.
        
        Edge case: First run when no config file exists yet.
        """
        config = ConfigManager()
        # Should not raise even if file doesn't exist
        config.read_local_config(update_config=False, validate=True)

    def test_read_local_config_with_update(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that read_local_config with update_config syncs to file."""
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        config = ConfigManager()
        config.read_local_config(update_config=True, validate=True)

        # File should now exist
        assert config_file.exists()

    def test_read_local_config_loads_values(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that read_local_config loads values from file."""
        config_file = tmp_path / "test_config.yaml"
        test_data = {"UI_WIDTH": 1024, "MAKER_NAME": "TestMaker"}
        with config_file.open("w", encoding="UTF-8") as f:
            yaml.dump(test_data, f)

        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        config = ConfigManager()
        config.read_local_config(update_config=False, validate=True)

        assert config.UI_WIDTH == 1024
        assert config.MAKER_NAME == "TestMaker"


class TestConfigManagerSyncConfigToFile:
    """Tests for ConfigManager.sync_config_to_file() method."""

    def test_sync_config_to_file_creates_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that sync_config_to_file creates the config file."""
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        config = ConfigManager()
        config.sync_config_to_file()

        assert config_file.exists()

    def test_sync_config_to_file_writes_valid_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that sync_config_to_file writes valid YAML."""
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        config = ConfigManager()
        config.sync_config_to_file()

        # Should be able to load the file as YAML
        with config_file.open("r", encoding="UTF-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)

    def test_sync_config_to_file_preserves_all_configs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that sync_config_to_file includes all configured values."""
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        config = ConfigManager()
        config.sync_config_to_file()

        with config_file.open("r", encoding="UTF-8") as f:
            data = yaml.safe_load(f)

        # Should have all the keys from config_type
        for key in config.config_type.keys():
            assert key in data


class TestConfigManagerAddConfig:
    """Tests for ConfigManager.add_config() method."""

    def test_add_config_string(self) -> None:
        """Test adding a string configuration."""
        config = ConfigManager()
        config.add_config("TEST_STRING", "default_value")
        assert hasattr(config, "TEST_STRING")
        assert config.TEST_STRING == "default_value"
        assert "TEST_STRING" in config.config_type

    def test_add_config_int(self) -> None:
        """Test adding an integer configuration."""
        config = ConfigManager()
        config.add_config("TEST_INT", 42)
        assert config.TEST_INT == 42
        assert isinstance(config.config_type["TEST_INT"], IntType)

    def test_add_config_float(self) -> None:
        """Test adding a float configuration."""
        config = ConfigManager()
        config.add_config("TEST_FLOAT", 3.14)
        assert config.TEST_FLOAT == 3.14

    def test_add_config_bool(self) -> None:
        """Test adding a boolean configuration."""
        config = ConfigManager()
        config.add_config("TEST_BOOL", True)
        assert config.TEST_BOOL is True

    def test_add_config_list_int(self) -> None:
        """Test adding a list of integers configuration."""
        config = ConfigManager()
        config.add_config("TEST_LIST", [1, 2, 3])
        assert config.TEST_LIST == [1, 2, 3]

    def test_add_config_list_with_min_length(self) -> None:
        """Test adding a list with minimum length requirement."""
        config = ConfigManager()
        config.add_config("TEST_LIST", [1, 2, 3], min_length=2)
        # Should validate successfully
        config.config_type["TEST_LIST"].validate("TEST_LIST", [1, 2, 3])
        # Should fail with too few elements
        with pytest.raises(ConfigError):
            config.config_type["TEST_LIST"].validate("TEST_LIST", [1])

    def test_add_config_empty_list_with_type(self) -> None:
        """Test adding an empty list with explicit type.
        
        Edge case: Empty lists need explicit type since type can't be inferred.
        """
        config = ConfigManager()
        config.add_config("TEST_EMPTY_LIST", [], list_type=int)
        assert config.TEST_EMPTY_LIST == []

    def test_add_config_with_validation_function(self) -> None:
        """Test adding config with custom validation."""

        def positive_validator(configname: str, value: int) -> None:
            if value <= 0:
                raise ConfigError(f"{configname} must be positive")

        config = ConfigManager()
        config.add_config("TEST_POSITIVE", 10, validation_function=[positive_validator])
        # Valid value should work
        config.config_type["TEST_POSITIVE"].validate("TEST_POSITIVE", 5)
        # Invalid value should fail
        with pytest.raises(ConfigError, match="must be positive"):
            config.config_type["TEST_POSITIVE"].validate("TEST_POSITIVE", -1)

    def test_add_config_preserves_existing_value(self) -> None:
        """Test that add_config doesn't overwrite existing attribute.
        
        Edge case: Used for addon configs that might already be set.
        """
        config = ConfigManager()
        config.EXISTING_CONFIG = "existing_value"
        config.add_config("EXISTING_CONFIG", "new_default")
        assert config.EXISTING_CONFIG == "existing_value"


class TestConfigManagerAddSelectionConfig:
    """Tests for ConfigManager.add_selection_config() method."""

    def test_add_selection_config_with_default(self) -> None:
        """Test adding a selection config with default value."""
        config = ConfigManager()
        config.add_selection_config("TEST_SELECT", ["opt1", "opt2", "opt3"], default_value="opt2")
        assert config.TEST_SELECT == "opt2"

    def test_add_selection_config_uses_first_as_default(self) -> None:
        """Test that first option is used as default when not specified."""
        config = ConfigManager()
        config.add_selection_config("TEST_SELECT", ["opt1", "opt2", "opt3"])
        assert config.TEST_SELECT == "opt1"

    def test_add_selection_config_validates_options(self) -> None:
        """Test that selection config only accepts allowed values."""
        config = ConfigManager()
        config.add_selection_config("TEST_SELECT", ["opt1", "opt2"])
        # Valid option should work
        config.config_type["TEST_SELECT"].validate("TEST_SELECT", "opt1")
        # Invalid option should fail
        with pytest.raises(ConfigError, match="is not supported"):
            config.config_type["TEST_SELECT"].validate("TEST_SELECT", "opt3")

    def test_add_selection_config_with_validator(self) -> None:
        """Test adding selection config with custom validator."""

        def no_test_validator(configname: str, value: str) -> None:
            if "test" in value.lower():
                raise ConfigError(f"{configname} cannot contain 'test'")

        config = ConfigManager()
        config.add_selection_config(
            "TEST_SELECT", ["production", "test_mode"], validation_function=[no_test_validator]
        )
        # Valid value
        config.config_type["TEST_SELECT"].validate("TEST_SELECT", "production")
        # Invalid value
        with pytest.raises(ConfigError, match="cannot contain"):
            config.config_type["TEST_SELECT"].validate("TEST_SELECT", "test_mode")


class TestConfigManagerChooseBottleNumber:
    """Tests for ConfigManager.choose_bottle_number() method."""

    def test_choose_bottle_number_default(self) -> None:
        """Test choose_bottle_number returns configured value limited by max."""
        config = ConfigManager()
        config.MAKER_NUMBER_BOTTLES = 10
        from src import MAX_SUPPORTED_BOTTLES

        result = config.choose_bottle_number()
        assert result == min(10, MAX_SUPPORTED_BOTTLES)

    def test_choose_bottle_number_ignore_limits(self) -> None:
        """Test choose_bottle_number with ignore_limits returns actual value."""
        config = ConfigManager()
        config.MAKER_NUMBER_BOTTLES = 10
        result = config.choose_bottle_number(ignore_limits=True)
        assert result == 10

    def test_choose_bottle_number_get_all(self) -> None:
        """Test choose_bottle_number with get_all returns max supported."""
        config = ConfigManager()
        from src import MAX_SUPPORTED_BOTTLES

        result = config.choose_bottle_number(get_all=True)
        assert result == MAX_SUPPORTED_BOTTLES


class TestIntegrationConfigDumpAndLoad:
    """Integration tests for dumping and loading complete configuration.
    
    These tests ensure the full config lifecycle works correctly.
    """

    def test_dump_and_load_default_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default config can be dumped and loaded successfully.
        
        This is the main integration test verifying the complete config lifecycle.
        """
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        # Create config and save it
        config1 = ConfigManager()
        original_width = config1.UI_WIDTH
        original_name = config1.MAKER_NAME
        config1.sync_config_to_file()

        # Load config in new instance
        config2 = ConfigManager()
        config2.read_local_config(update_config=False, validate=True)

        # Values should match
        assert config2.UI_WIDTH == original_width
        assert config2.MAKER_NAME == original_name

    def test_dump_and_load_modified_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that modified config values persist through dump and load."""
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        # Create and modify config
        config1 = ConfigManager()
        config1.UI_WIDTH = 1920
        config1.UI_HEIGHT = 1080
        config1.MAKER_NAME = "MyCustomMaker"
        config1.sync_config_to_file()

        # Load in new instance
        config2 = ConfigManager()
        config2.read_local_config(update_config=False, validate=True)

        # Modified values should persist
        assert config2.UI_WIDTH == 1920
        assert config2.UI_HEIGHT == 1080
        assert config2.MAKER_NAME == "MyCustomMaker"

    def test_dump_and_load_pump_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that complex PumpConfig objects survive dump and load cycle."""
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        # Create config with custom pump settings
        # Need to set MAKER_NUMBER_BOTTLES first since PUMP_CONFIG min_length depends on it
        config1 = ConfigManager()
        config1.MAKER_NUMBER_BOTTLES = 2
        config1.PUMP_CONFIG = [
            PumpConfig(pin=10, volume_flow=20.5, tube_volume=5),
            PumpConfig(pin=11, volume_flow=25.0, tube_volume=6),
        ]
        config1.sync_config_to_file()

        # Load in new instance
        config2 = ConfigManager()
        config2.read_local_config(update_config=False, validate=True)

        # Pump configs should match
        assert len(config2.PUMP_CONFIG) == 2
        assert config2.PUMP_CONFIG[0].pin == 10
        assert config2.PUMP_CONFIG[0].volume_flow == 20.5
        assert config2.PUMP_CONFIG[0].tube_volume == 5
        assert config2.PUMP_CONFIG[1].pin == 11
        assert config2.PUMP_CONFIG[1].volume_flow == 25.0
        assert config2.PUMP_CONFIG[1].tube_volume == 6

    def test_load_config_with_new_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that loading old config file gets new default values.
        
        Edge case: Simulates upgrade scenario where new config keys are added.
        """
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        # Create minimal config file (like from old version)
        minimal_config = {"UI_WIDTH": 800}
        with config_file.open("w", encoding="UTF-8") as f:
            yaml.dump(minimal_config, f)

        # Load config
        config = ConfigManager()
        config.read_local_config(update_config=True, validate=True)

        # Old value should be loaded
        assert config.UI_WIDTH == 800
        # New values should have defaults
        assert hasattr(config, "MAKER_NAME")
        assert hasattr(config, "UI_HEIGHT")

        # Sync should add new keys to file
        with config_file.open("r", encoding="UTF-8") as f:
            updated_config = yaml.safe_load(f)
        assert "MAKER_NAME" in updated_config
        assert "UI_HEIGHT" in updated_config

    def test_config_handles_corrupted_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config with invalid values falls back to defaults.
        
        Edge case: Handles manually edited config files with errors.
        """
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        # Create config with invalid value
        invalid_config = {"UI_WIDTH": "not_a_number", "MAKER_NAME": "ValidName"}
        with config_file.open("w", encoding="UTF-8") as f:
            yaml.dump(invalid_config, f)

        # Load without validation should not raise
        config = ConfigManager()
        config.read_local_config(update_config=False, validate=False)

        # Invalid value should not have been set (keeps default)
        assert isinstance(config.UI_WIDTH, int)
        # Valid value should be set
        assert config.MAKER_NAME == "ValidName"


class TestEdgeCasesConfigManager:
    """Edge case tests for ConfigManager.
    
    These tests ensure the config system handles unusual scenarios gracefully.
    """

    def test_config_validates_with_validators_module(self) -> None:
        """Test that built-in validators from validators module work correctly."""
        from src.config.validators import build_number_limiter, validate_max_length

        config = ConfigManager()

        # Test number limiter
        limiter = build_number_limiter(1, 100)
        limiter("test", 50)  # Should not raise
        with pytest.raises(ConfigError):
            limiter("test", 150)

        # Test max length validator
        validate_max_length("test", "short")  # Should not raise
        with pytest.raises(ConfigError):
            validate_max_length("test", "x" * 100)

    def test_config_handles_list_with_callable_min_length(self) -> None:
        """Test that list configs with callable min_length work correctly.
        
        Edge case: Some list lengths depend on other config values.
        """
        config = ConfigManager()
        config.MAKER_NUMBER_BOTTLES = 5

        # PUMP_CONFIG uses a callable for min_length
        pump_list = config.config_type["PUMP_CONFIG"]
        min_len = pump_list.min_length() if callable(pump_list.min_length) else pump_list.min_length

        # Should use the value from choose_bottle_number
        assert min_len == config.choose_bottle_number(ignore_limits=True)

    def test_get_config_with_ui_information(self) -> None:
        """Test that get_config_with_ui_information includes UI metadata.
        
        This is used by the web UI to render config forms.
        """
        config = ConfigManager()
        result = config.get_config_with_ui_information()

        # Should have UI information for each config
        assert "UI_WIDTH" in result
        config_info = result["UI_WIDTH"]
        assert "value" in config_info
        assert "description" in config_info

        # Choose types should have allowed values
        choose_config = result["UI_LANGUAGE"]
        assert "allowed" in choose_config

        # Bool types should have check_name
        bool_config = result["UI_DEVENVIRONMENT"]
        assert "check_name" in bool_config

    def test_config_preserves_type_through_serialization(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that all config types maintain correct types through save/load.
        
        Edge case: Ensures YAML serialization doesn't corrupt types.
        """
        config_file = tmp_path / "test_config.yaml"
        monkeypatch.setattr("src.config.config_manager.CUSTOM_CONFIG_FILE", config_file)

        config1 = ConfigManager()
        config1.sync_config_to_file()

        config2 = ConfigManager()
        config2.read_local_config(update_config=False, validate=True)

        # Check various types are preserved
        assert isinstance(config2.UI_DEVENVIRONMENT, bool)
        assert isinstance(config2.UI_WIDTH, int)
        assert isinstance(config2.MAKER_NAME, str)
        assert isinstance(config2.PUMP_CONFIG, list)
        assert isinstance(config2.MAKER_PREPARE_VOLUME, list)
