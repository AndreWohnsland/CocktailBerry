"""Tests for DynamicConfigType and LED configuration classes."""

from __future__ import annotations

import pytest

from src.config.config_types import (
    BoolType,
    ChooseType,
    DictType,
    DynamicConfigType,
    IntType,
    ListType,
    NormalLedConfig,
    WS281xLedConfig,
)
from src.config.errors import ConfigError


class TestNormalLedConfig:
    """Tests for NormalLedConfig class."""

    def test_init_and_to_config(self) -> None:
        """Test NormalLedConfig initialization and serialization."""
        config = NormalLedConfig(
            led_type="normal",
            pins=[14, 15],
            brightness=100,
            default_on=True,
            preparation_state="Effect",
        )
        
        assert config.led_type == "normal"
        assert config.pins == [14, 15]
        assert config.brightness == 100
        assert config.default_on is True
        assert config.preparation_state == "Effect"
        
        # Test serialization
        config_dict = config.to_config()
        assert config_dict == {
            "led_type": "normal",
            "pins": [14, 15],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }

    def test_from_config(self) -> None:
        """Test NormalLedConfig deserialization."""
        config_dict = {
            "led_type": "normal",
            "pins": [18, 23],
            "brightness": 200,
            "default_on": False,
            "preparation_state": "On",
        }
        
        config = NormalLedConfig.from_config(config_dict)
        
        assert config.led_type == "normal"
        assert config.pins == [18, 23]
        assert config.brightness == 200
        assert config.default_on is False
        assert config.preparation_state == "On"


class TestWS281xLedConfig:
    """Tests for WS281xLedConfig class."""

    def test_init_and_to_config(self) -> None:
        """Test WS281xLedConfig initialization and serialization."""
        config = WS281xLedConfig(
            led_type="ws281x",
            pins=[18],
            brightness=150,
            count=30,
            number_rings=2,
            default_on=False,
            preparation_state="Effect",
        )
        
        assert config.led_type == "ws281x"
        assert config.pins == [18]
        assert config.brightness == 150
        assert config.count == 30
        assert config.number_rings == 2
        assert config.default_on is False
        assert config.preparation_state == "Effect"
        
        # Test serialization
        config_dict = config.to_config()
        assert config_dict == {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            "count": 30,
            "number_rings": 2,
            "default_on": False,
            "preparation_state": "Effect",
        }

    def test_from_config(self) -> None:
        """Test WS281xLedConfig deserialization."""
        config_dict = {
            "led_type": "ws281x",
            "pins": [12],
            "brightness": 255,
            "count": 24,
            "number_rings": 1,
            "default_on": True,
            "preparation_state": "On",
        }
        
        config = WS281xLedConfig.from_config(config_dict)
        
        assert config.led_type == "ws281x"
        assert config.pins == [12]
        assert config.brightness == 255
        assert config.count == 24
        assert config.number_rings == 1
        assert config.default_on is True
        assert config.preparation_state == "On"


class TestDynamicConfigType:
    """Tests for DynamicConfigType class."""

    @pytest.fixture
    def led_dynamic_type(self) -> DynamicConfigType:
        """Create a DynamicConfigType for LED configuration."""
        return DynamicConfigType(
            discriminator_field="led_type",
            type_mapping={
                "normal": DictType(
                    {
                        "led_type": ChooseType(allowed=["normal", "ws281x"]),
                        "pins": ListType(IntType(), 0),
                        "brightness": IntType(),
                        "default_on": BoolType(),
                        "preparation_state": ChooseType(allowed=["On", "Off", "Effect"]),
                    },
                    NormalLedConfig,
                ),
                "ws281x": DictType(
                    {
                        "led_type": ChooseType(allowed=["normal", "ws281x"]),
                        "pins": ListType(IntType(), 0),
                        "brightness": IntType(),
                        "count": IntType(),
                        "number_rings": IntType(),
                        "default_on": BoolType(),
                        "preparation_state": ChooseType(allowed=["On", "Off", "Effect"]),
                    },
                    WS281xLedConfig,
                ),
            },
        )

    def test_get_discriminator_options(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test getting discriminator options."""
        options = led_dynamic_type.get_discriminator_options()
        assert set(options) == {"normal", "ws281x"}

    def test_get_schema_for_type(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test getting schema for a specific type."""
        normal_schema = led_dynamic_type.get_schema_for_type("normal")
        assert normal_schema is not None
        assert "led_type" in normal_schema
        assert "pins" in normal_schema
        assert "brightness" in normal_schema
        assert "default_on" in normal_schema
        assert "preparation_state" in normal_schema
        assert "count" not in normal_schema  # WS281x specific field
        
        ws281x_schema = led_dynamic_type.get_schema_for_type("ws281x")
        assert ws281x_schema is not None
        assert "count" in ws281x_schema
        assert "number_rings" in ws281x_schema

    def test_validate_normal_led_success(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test validation of normal LED config."""
        config_dict = {
            "led_type": "normal",
            "pins": [14, 15],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }
        
        # Should not raise
        led_dynamic_type.validate("test_config", config_dict)

    def test_validate_ws281x_led_success(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test validation of WS281x LED config."""
        config_dict = {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            "count": 30,
            "number_rings": 2,
            "default_on": False,
            "preparation_state": "On",
        }
        
        # Should not raise
        led_dynamic_type.validate("test_config", config_dict)

    def test_validate_missing_discriminator(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test validation fails when discriminator field is missing."""
        config_dict = {
            "pins": [14],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }
        
        with pytest.raises(ConfigError, match="missing discriminator field"):
            led_dynamic_type.validate("test_config", config_dict)

    def test_validate_invalid_discriminator_value(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test validation fails when discriminator value is invalid."""
        config_dict = {
            "led_type": "invalid_type",
            "pins": [14],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }
        
        with pytest.raises(ConfigError, match="invalid led_type"):
            led_dynamic_type.validate("test_config", config_dict)

    def test_validate_missing_required_field(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test validation fails when required field is missing."""
        config_dict = {
            "led_type": "normal",
            "pins": [14],
            # Missing brightness, default_on, preparation_state
        }
        
        with pytest.raises(ConfigError, match="is missing"):
            led_dynamic_type.validate("test_config", config_dict)

    def test_validate_ws281x_missing_specific_field(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test validation fails when WS281x-specific field is missing."""
        config_dict = {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            # Missing count and number_rings
            "default_on": False,
            "preparation_state": "On",
        }
        
        with pytest.raises(ConfigError, match="is missing"):
            led_dynamic_type.validate("test_config", config_dict)

    def test_from_config_normal(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test deserializing normal LED config."""
        config_dict = {
            "led_type": "normal",
            "pins": [14, 15],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }
        
        config = led_dynamic_type.from_config(config_dict)
        
        assert isinstance(config, NormalLedConfig)
        assert config.led_type == "normal"
        assert config.pins == [14, 15]
        assert config.brightness == 100

    def test_from_config_ws281x(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test deserializing WS281x LED config."""
        config_dict = {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            "count": 30,
            "number_rings": 2,
            "default_on": False,
            "preparation_state": "On",
        }
        
        config = led_dynamic_type.from_config(config_dict)
        
        assert isinstance(config, WS281xLedConfig)
        assert config.led_type == "ws281x"
        assert config.pins == [18]
        assert config.count == 30
        assert config.number_rings == 2

    def test_to_config_normal(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test serializing normal LED config."""
        config = NormalLedConfig(
            led_type="normal",
            pins=[14, 15],
            brightness=100,
            default_on=True,
            preparation_state="Effect",
        )
        
        config_dict = led_dynamic_type.to_config(config)
        
        assert config_dict == {
            "led_type": "normal",
            "pins": [14, 15],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }

    def test_to_config_ws281x(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test serializing WS281x LED config."""
        config = WS281xLedConfig(
            led_type="ws281x",
            pins=[18],
            brightness=150,
            count=30,
            number_rings=2,
            default_on=False,
            preparation_state="On",
        )
        
        config_dict = led_dynamic_type.to_config(config)
        
        assert config_dict == {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            "count": 30,
            "number_rings": 2,
            "default_on": False,
            "preparation_state": "On",
        }

    def test_roundtrip_normal(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test roundtrip serialization/deserialization for normal LED."""
        original_dict = {
            "led_type": "normal",
            "pins": [14, 15],
            "brightness": 100,
            "default_on": True,
            "preparation_state": "Effect",
        }
        
        config = led_dynamic_type.from_config(original_dict)
        roundtrip_dict = led_dynamic_type.to_config(config)
        
        assert original_dict == roundtrip_dict

    def test_roundtrip_ws281x(self, led_dynamic_type: DynamicConfigType) -> None:
        """Test roundtrip serialization/deserialization for WS281x LED."""
        original_dict = {
            "led_type": "ws281x",
            "pins": [18],
            "brightness": 150,
            "count": 30,
            "number_rings": 2,
            "default_on": False,
            "preparation_state": "On",
        }
        
        config = led_dynamic_type.from_config(original_dict)
        roundtrip_dict = led_dynamic_type.to_config(config)
        
        assert original_dict == roundtrip_dict
