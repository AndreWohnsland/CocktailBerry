"""Tests for configuration type classes.

This module tests the serialization, deserialization, and validation of various config types.
"""

from __future__ import annotations

import pytest

from src.config.config_types import BoolType, ChooseType, DictType, FloatType, IntType, ListType, PumpConfig, StringType
from src.config.errors import ConfigError


class TestStringType:
    """Tests for StringType config class."""

    def test_validation_success(self) -> None:
        """Test that valid string values pass validation."""
        string_type = StringType()
        string_type.validate("test_config", "valid_string")

    def test_validation_fails_for_non_string(self) -> None:
        """Test that non-string values fail validation."""
        string_type = StringType()
        with pytest.raises(ConfigError, match="is not of type"):
            string_type.validate("test_config", 123)

    def test_validation_with_custom_validator(self) -> None:
        """Test string validation with custom validator function."""

        def length_validator(configname: str, value: str) -> None:
            if len(value) > 10:
                raise ConfigError(f"{configname} is too long")

        string_type = StringType([length_validator])
        string_type.validate("test_config", "short")
        with pytest.raises(ConfigError, match="too long"):
            string_type.validate("test_config", "this_is_way_too_long")

    def test_serialization(self) -> None:
        """Test string serialization (to_config)."""
        string_type = StringType()
        assert string_type.to_config("test_value") == "test_value"

    def test_deserialization(self) -> None:
        """Test string deserialization (from_config)."""
        string_type = StringType()
        assert string_type.from_config("test_value") == "test_value"

    def test_prefix_suffix(self) -> None:
        """Test that prefix and suffix are properly stored."""
        string_type = StringType(prefix="Pre:", suffix="suf")
        assert string_type.prefix == "Pre:"
        assert string_type.suffix == "suf"


class TestIntType:
    """Tests for IntType config class."""

    def test_validation_success(self) -> None:
        """Test that valid integer values pass validation."""
        int_type = IntType()
        int_type.validate("test_config", 42)

    def test_validation_fails_for_non_int(self) -> None:
        """Test that non-integer values fail validation."""
        int_type = IntType()
        with pytest.raises(ConfigError, match="is not of type"):
            int_type.validate("test_config", "not_an_int")

    def test_validation_with_limiter(self) -> None:
        """Test integer validation with range limiter."""

        def range_limiter(configname: str, value: int) -> None:
            if value < 1 or value > 100:
                raise ConfigError(f"{configname} must be between 1 and 100")

        int_type = IntType([range_limiter])
        int_type.validate("test_config", 50)
        with pytest.raises(ConfigError, match="must be between"):
            int_type.validate("test_config", 150)

    def test_serialization(self) -> None:
        """Test integer serialization (to_config)."""
        int_type = IntType()
        assert int_type.to_config(42) == 42

    def test_deserialization(self) -> None:
        """Test integer deserialization (from_config)."""
        int_type = IntType()
        assert int_type.from_config(42) == 42

    def test_prefix_suffix(self) -> None:
        """Test that prefix and suffix are properly stored."""
        int_type = IntType(prefix="Value:", suffix="px")
        assert int_type.prefix == "Value:"
        assert int_type.suffix == "px"


class TestFloatType:
    """Tests for FloatType config class."""

    def test_validation_success_with_float(self) -> None:
        """Test that valid float values pass validation."""
        float_type = FloatType()
        float_type.validate("test_config", 3.14)

    def test_validation_success_with_int(self) -> None:
        """Test that integer values are accepted as floats."""
        float_type = FloatType()
        float_type.validate("test_config", 42)

    def test_validation_fails_for_non_number(self) -> None:
        """Test that non-numeric values fail validation."""
        float_type = FloatType()
        with pytest.raises(ConfigError, match="is not of type"):
            float_type.validate("test_config", "not_a_float")

    def test_validation_with_limiter(self) -> None:
        """Test float validation with range limiter."""

        def range_limiter(configname: str, value: float) -> None:
            if value < 0.0 or value > 1.0:
                raise ConfigError(f"{configname} must be between 0.0 and 1.0")

        float_type = FloatType([range_limiter])
        float_type.validate("test_config", 0.5)
        with pytest.raises(ConfigError, match="must be between"):
            float_type.validate("test_config", 1.5)

    def test_serialization_float(self) -> None:
        """Test float serialization (to_config) with float value."""
        float_type = FloatType()
        assert float_type.to_config(3.14) == pytest.approx(3.14)

    def test_serialization_int_to_float(self) -> None:
        """Test that integers are converted to float on serialization."""
        float_type = FloatType()
        result = float_type.to_config(42)
        assert result == pytest.approx(42.0)
        assert isinstance(result, float)

    def test_deserialization(self) -> None:
        """Test float deserialization (from_config)."""
        float_type = FloatType()
        assert float_type.from_config(3.14) == pytest.approx(3.14)


class TestBoolType:
    """Tests for BoolType config class."""

    def test_validation_success(self) -> None:
        """Test that valid boolean values pass validation."""
        bool_type = BoolType()
        bool_type.validate("test_config", True)
        bool_type.validate("test_config", False)

    def test_validation_fails_for_non_bool(self) -> None:
        """Test that non-boolean values fail validation."""
        bool_type = BoolType()
        with pytest.raises(ConfigError, match="is not of type"):
            bool_type.validate("test_config", 1)
        with pytest.raises(ConfigError, match="is not of type"):
            bool_type.validate("test_config", "true")

    def test_serialization(self) -> None:
        """Test boolean serialization (to_config)."""
        bool_type = BoolType()
        assert bool_type.to_config(True) is True
        assert bool_type.to_config(False) is False

    def test_deserialization(self) -> None:
        """Test boolean deserialization (from_config)."""
        bool_type = BoolType()
        assert bool_type.from_config(True) is True
        assert bool_type.from_config(False) is False

    def test_check_name(self) -> None:
        """Test that check_name attribute is properly stored."""
        bool_type = BoolType(check_name="Enable Feature")
        assert bool_type.check_name == "Enable Feature"

    def test_default_check_name(self) -> None:
        """Test default check_name value."""
        bool_type = BoolType()
        assert bool_type.check_name == "on"


class TestChooseType:
    """Tests for ChooseType config class."""

    def test_validation_success(self) -> None:
        """Test that values in allowed list pass validation."""
        choose_type = ChooseType(allowed=["option1", "option2", "option3"])
        choose_type.validate("test_config", "option1")
        choose_type.validate("test_config", "option2")

    def test_validation_fails_for_invalid_choice(self) -> None:
        """Test that values not in allowed list fail validation."""
        choose_type = ChooseType(allowed=["option1", "option2"])
        with pytest.raises(ConfigError, match="is not supported"):
            choose_type.validate("test_config", "invalid_option")

    def test_validation_with_custom_validator(self) -> None:
        """Test choose validation with custom validator function."""

        def custom_validator(configname: str, value: str) -> None:
            if value == "forbidden":
                raise ConfigError(f"{configname} cannot be 'forbidden'")

        choose_type = ChooseType(allowed=["forbidden", "allowed"], validator_functions=[custom_validator])
        choose_type.validate("test_config", "allowed")
        with pytest.raises(ConfigError, match="cannot be 'forbidden'"):
            choose_type.validate("test_config", "forbidden")

    def test_serialization(self) -> None:
        """Test choose serialization (to_config)."""
        choose_type = ChooseType(allowed=["a", "b"])
        assert choose_type.to_config("a") == "a"

    def test_deserialization(self) -> None:
        """Test choose deserialization (from_config)."""
        choose_type = ChooseType(allowed=["a", "b"])
        assert choose_type.from_config("b") == "b"


class TestListType:
    """Tests for ListType config class."""

    def test_validation_success(self) -> None:
        """Test that valid lists pass validation."""
        list_type = ListType(IntType(), 2)
        list_type.validate("test_config", [1, 2, 3])

    def test_validation_fails_for_non_list(self) -> None:
        """Test that non-list values fail validation."""
        list_type = ListType(IntType(), 0)
        with pytest.raises(ConfigError, match="is not of type"):
            list_type.validate("test_config", "not_a_list")

    def test_validation_fails_for_min_length(self) -> None:
        """Test that lists shorter than min_length fail validation."""
        list_type = ListType(IntType(), 3)
        with pytest.raises(ConfigError, match="need at least 3 elements"):
            list_type.validate("test_config", [1, 2])

    def test_validation_with_callable_min_length(self) -> None:
        """Test min_length as a callable function.

        This is used when the min length depends on other config values.
        """

        def min_length_func():
            return 5

        list_type = ListType(IntType(), min_length_func)
        list_type.validate("test_config", [1, 2, 3, 4, 5])
        with pytest.raises(ConfigError, match="need at least 5 elements"):
            list_type.validate("test_config", [1, 2, 3])

    def test_validation_fails_for_invalid_item_type(self) -> None:
        """Test that list items of wrong type fail validation."""
        list_type = ListType(IntType(), 0)
        with pytest.raises(ConfigError, match="is not of type"):
            list_type.validate("test_config", [1, 2, "not_an_int"])

    def test_serialization(self) -> None:
        """Test list serialization (to_config)."""
        list_type = ListType(IntType(), 0)
        assert list_type.to_config([1, 2, 3]) == [1, 2, 3]

    def test_serialization_with_float_conversion(self) -> None:
        """Test list serialization converts int to float for FloatType."""
        list_type = ListType(FloatType(), 0)
        result = list_type.to_config([1, 2, 3])
        assert result == [1.0, 2.0, 3.0]
        assert all(isinstance(x, float) for x in result)

    def test_deserialization(self) -> None:
        """Test list deserialization (from_config)."""
        list_type = ListType(IntType(), 0)
        assert list_type.from_config([1, 2, 3]) == [1, 2, 3]

    def test_immutable_flag(self) -> None:
        """Test that immutable flag is properly stored."""
        list_type = ListType(IntType(), 0, immutable=True)
        assert list_type.immutable is True


class TestDictType:
    """Tests for DictType config class."""

    def test_validation_success(self) -> None:
        """Test that valid dictionaries pass validation."""
        dict_type = DictType({"name": StringType(), "age": IntType()}, PumpConfig)
        dict_type.validate("test_config", {"name": "John", "age": 30})

    def test_validation_fails_for_missing_key(self) -> None:
        """Test that dictionaries missing required keys fail validation."""
        dict_type = DictType({"name": StringType(), "age": IntType()}, PumpConfig)
        with pytest.raises(ConfigError, match="is missing"):
            dict_type.validate("test_config", {"name": "John"})

    def test_validation_fails_for_invalid_value_type(self) -> None:
        """Test that dictionaries with wrong value types fail validation."""
        dict_type = DictType({"name": StringType(), "age": IntType()}, PumpConfig)
        with pytest.raises(ConfigError, match="is not of type"):
            dict_type.validate("test_config", {"name": "John", "age": "thirty"})

    def test_serialization(self) -> None:
        """Test dict serialization (to_config) using PumpConfig."""
        dict_type = DictType(
            {"pin": IntType(), "volume_flow": FloatType(), "tube_volume": IntType()},
            PumpConfig,
        )
        pump = PumpConfig(pin=1, volume_flow=2.5, tube_volume=10)
        result = dict_type.to_config(pump)
        assert result["pin"] == 1
        assert result["volume_flow"] == pytest.approx(2.5)
        assert result["tube_volume"] == 10

    def test_deserialization(self) -> None:
        """Test dict deserialization (from_config) creates PumpConfig."""
        dict_type = DictType(
            {"pin": IntType(), "volume_flow": FloatType(), "tube_volume": IntType()},
            PumpConfig,
        )
        config_dict = {"pin": 1, "volume_flow": 2.5, "tube_volume": 10}
        result = dict_type.from_config(config_dict)
        assert isinstance(result, PumpConfig)
        assert result.pin == 1
        assert result.volume_flow == pytest.approx(2.5)
        assert result.tube_volume == 10


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


class TestEdgeCases:
    """Edge case tests for config types.

    These tests cover unusual but valid scenarios that might occur in production.
    """

    def test_empty_list_with_zero_min_length(self) -> None:
        """Test that empty lists are allowed when min_length is 0.

        Edge case: Some configs might have optional list values.
        """
        list_type = ListType(IntType(), 0)
        list_type.validate("test_config", [])

    def test_list_with_nested_validation(self) -> None:
        """Test list validation with nested validators on list items.

        Edge case: Ensures validators cascade properly through list items.
        """

        def positive_validator(configname: str, value: int) -> None:
            if value <= 0:
                raise ConfigError(f"{configname} must be positive")

        list_type = ListType(IntType([positive_validator]), 1)
        list_type.validate("test_config", [1, 2, 3])
        with pytest.raises(ConfigError, match="must be positive"):
            list_type.validate("test_config", [1, -1, 3])

    def test_float_type_precision(self) -> None:
        """Test that float type preserves precision.

        Edge case: Ensures no unexpected rounding in config values.
        """
        float_type = FloatType()
        value = 3.141592653589793
        serialized = float_type.to_config(value)
        assert serialized == pytest.approx(value)

    def test_choose_type_empty_allowed_list(self) -> None:
        """Test ChooseType behavior with empty allowed list.

        Edge case: Any value should fail validation if no options are allowed.
        """
        choose_type = ChooseType(allowed=[])
        with pytest.raises(ConfigError, match="is not supported"):
            choose_type.validate("test_config", "anything")

    def test_dict_type_extra_keys_ignored(self) -> None:
        """Test that DictType only validates required keys.

        Edge case: Config files might have extra keys from future versions.
        """
        dict_types = {"required": StringType()}
        dict_type = DictType(dict_types, PumpConfig)
        # Should not fail even with extra keys
        dict_type.validate("test_config", {"required": "value", "extra": "ignored"})

    def test_string_type_empty_string(self) -> None:
        """Test that empty strings are valid by default.

        Edge case: Some configs might intentionally be empty strings.
        """
        string_type = StringType()
        string_type.validate("test_config", "")

    def test_list_type_single_element(self) -> None:
        """Test list with exactly one element at minimum length.

        Edge case: Boundary condition for min_length validation.
        """
        list_type = ListType(StringType(), 1)
        list_type.validate("test_config", ["single"])
        string_type = StringType()
        string_type.validate("test_config", "")
