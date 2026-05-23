"""Tests for DiscriminatedDictType and polymorphic pump config hierarchy."""

from __future__ import annotations

from typing import Any

import pytest

from src.config.config_manager import ConfigManager
from src.config.config_types import (
    BasePumpConfig,
    ChooseOptions,
    ChooseType,
    ConfigClass,
    DCGPIOPumpConfig,
    DCI2CPumpConfig,
    DCPumpConfig,
    DictType,
    DiscriminatedDictType,
    FloatType,
    GlobalGPIOReversionConfig,
    GlobalI2CReversionConfig,
    IntType,
    ListType,
    StepperPumpConfig,
    StringType,
)
from src.config.errors import ConfigError


def _build_pump_discriminated_type() -> DiscriminatedDictType:
    """Build a DiscriminatedDictType matching the PUMP_CONFIG definition."""
    return DiscriminatedDictType(
        "pump_type",
        {
            "DC over GPIO": DictType(
                {
                    "pump_type": ChooseOptions.dispenser,
                    "pin": IntType(),
                    "volume_flow": FloatType(),
                    "tube_volume": IntType(),
                },
                DCGPIOPumpConfig,
            ),
            "DC over I2C": DictType(
                {
                    "pump_type": ChooseOptions.dispenser,
                    "pin_type": ChooseOptions.i2c,
                    "board_number": IntType(default=1),
                    "pin": IntType(),
                    "volume_flow": FloatType(),
                    "tube_volume": IntType(),
                },
                DCI2CPumpConfig,
            ),
            "Stepper": DictType(
                {
                    "pump_type": ChooseOptions.dispenser,
                    "pin": IntType(),
                    "dir_pin": IntType(),
                    "enable_pin": IntType(default=-1),
                    "driver_type": ChooseOptions.stepper_driver,
                    "step_type": ChooseOptions.stepper_step_type,
                    "volume_flow": FloatType(),
                    "tube_volume": IntType(),
                },
                StepperPumpConfig,
            ),
        },
    )


class TestDiscriminatedDictType:
    def test_dc_gpio_dispatch(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {
            "pump_type": "DC over GPIO",
            "pin": 14,
            "volume_flow": 30.0,
            "tube_volume": 5,
        }
        dt.validate("test", config_dict)
        result = dt.from_config(config_dict)
        # GPIO variant resolves to the dedicated subclass (still an isinstance match on the base).
        assert isinstance(result, DCGPIOPumpConfig)
        assert isinstance(result, DCPumpConfig)
        assert result.pin == 14
        assert result.volume_flow == pytest.approx(30.0)
        assert result.pump_type == "DC over GPIO"
        # The GPIO subclass does not carry pin_type / board_number as attributes.
        assert not hasattr(result, "pin_type")
        assert not hasattr(result, "board_number")

    def test_dc_i2c_dispatch(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {
            "pump_type": "DC over I2C",
            "pin_type": "MCP23017",
            "board_number": 2,
            "pin": 5,
            "volume_flow": 30.0,
            "tube_volume": 5,
        }
        dt.validate("test", config_dict)
        result = dt.from_config(config_dict)
        assert isinstance(result, DCI2CPumpConfig)
        assert isinstance(result, DCPumpConfig)
        assert result.pin == 5
        assert result.pump_type == "DC over I2C"
        assert result.pin_type == "MCP23017"
        assert result.board_number == 2

    def test_stepper_dispatch(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {
            "pump_type": "Stepper",
            "pin": 17,
            "dir_pin": 27,
            "driver_type": "DRV8825",
            "step_type": "Half",
            "volume_flow": 25.0,
            "tube_volume": 3,
        }
        dt.validate("test", config_dict)
        result = dt.from_config(config_dict)
        assert isinstance(result, StepperPumpConfig)
        assert result.pin == 17
        assert result.dir_pin == 27
        assert result.driver_type == "DRV8825"

    def test_unknown_discriminator_fails(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {"pump_type": "Unknown", "pin": 1}
        with pytest.raises(ConfigError, match="Unknown pump_type"):
            dt.validate("test", config_dict)

    def test_missing_discriminator_fails(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {"pin": 1, "volume_flow": 30.0}
        with pytest.raises(ConfigError, match="Missing discriminator"):
            dt.validate("test", config_dict)

    def test_stepper_wrong_field_type_fails(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {
            "pump_type": "Stepper",
            "pin": 17,
            "dir_pin": "not_a_number",
            "volume_flow": 25.0,
            "tube_volume": 0,
        }
        with pytest.raises(ConfigError, match="dir_pin"):
            dt.validate("test", config_dict)

    def test_dc_gpio_round_trip(self) -> None:
        dt = _build_pump_discriminated_type()
        original = DCGPIOPumpConfig(pin=14, volume_flow=30.0, tube_volume=5)
        serialized = dt.to_config(original)
        assert serialized["pump_type"] == "DC over GPIO"
        assert serialized["pin"] == 14
        # The GPIO subclass intentionally does not emit pin_type / board_number — the variant
        # discriminator alone tells the system how to route.
        assert "pin_type" not in serialized
        assert "board_number" not in serialized
        restored = dt.from_config(serialized)
        assert isinstance(restored, DCGPIOPumpConfig)
        assert restored.pin == original.pin
        assert restored.volume_flow == pytest.approx(original.volume_flow)

    def test_dc_i2c_round_trip(self) -> None:
        dt = _build_pump_discriminated_type()
        original = DCI2CPumpConfig(pin=5, volume_flow=30.0, tube_volume=5, pin_type="MCP23017", board_number=2)
        serialized = dt.to_config(original)
        assert serialized["pump_type"] == "DC over I2C"
        assert serialized["pin"] == 5
        assert serialized["pin_type"] == "MCP23017"
        assert serialized["board_number"] == 2
        restored = dt.from_config(serialized)
        assert isinstance(restored, DCI2CPumpConfig)
        assert restored.pin == original.pin
        assert restored.pin_type == "MCP23017"
        assert restored.board_number == 2

    def test_dc_gpio_pin_id_is_routed_via_gpio(self) -> None:
        # The class structure encodes the routing — DCGPIOPumpConfig's pin_id always uses GPIO.
        assert DCGPIOPumpConfig(pin=14).pin_id.pin_type == "GPIO"
        assert DCGPIOPumpConfig(pin=14).pin_id.board_number == 1

    def test_dc_i2c_pin_id_uses_configured_expander(self) -> None:
        pin_id = DCI2CPumpConfig(pin=5, pin_type="MCP23017", board_number=2).pin_id
        assert pin_id.pin_type == "MCP23017"
        assert pin_id.board_number == 2
        assert pin_id.pin == 5

    def test_stepper_round_trip(self) -> None:
        dt = _build_pump_discriminated_type()
        original = StepperPumpConfig(
            pin=17,
            dir_pin=27,
            driver_type="A4988",
            step_type="Full",
            volume_flow=25.0,
            tube_volume=3,
        )
        serialized = dt.to_config(original)
        assert serialized["pump_type"] == "Stepper"
        assert serialized["pin"] == 17
        restored = dt.from_config(serialized)
        assert isinstance(restored, StepperPumpConfig)
        assert restored.pin == original.pin
        assert restored.driver_type == original.driver_type

    def test_get_default_returns_first_variant(self) -> None:
        dt = _build_pump_discriminated_type()
        default = dt.get_default()
        assert isinstance(default, dict)
        assert "pump_type" in default


class TestBasePumpConfig:
    def test_dc_gpio_is_base(self) -> None:
        dc = DCGPIOPumpConfig(pin=14, volume_flow=30.0, tube_volume=5)
        assert isinstance(dc, DCPumpConfig)
        assert isinstance(dc, BasePumpConfig)

    def test_dc_i2c_is_base(self) -> None:
        dc = DCI2CPumpConfig(pin=5, volume_flow=30.0, tube_volume=5)
        assert isinstance(dc, DCPumpConfig)
        assert isinstance(dc, BasePumpConfig)

    def test_stepper_is_base(self) -> None:
        stepper = StepperPumpConfig(pin=17, dir_pin=27)
        assert isinstance(stepper, BasePumpConfig)

    def test_dc_gpio_shared_fields(self) -> None:
        dc = DCGPIOPumpConfig(pin=14, volume_flow=30.0, tube_volume=5)
        assert dc.pump_type == "DC over GPIO"
        assert dc.volume_flow == pytest.approx(30.0)
        assert dc.tube_volume == 5

    def test_stepper_shared_fields(self) -> None:
        stepper = StepperPumpConfig(pin=17, dir_pin=27, volume_flow=25.0, tube_volume=3)
        assert stepper.pump_type == "Stepper"
        assert stepper.volume_flow == pytest.approx(25.0)
        assert stepper.tube_volume == 3


class TestGlobalReversionConfig:
    def test_global_gpio_pin_id_is_routed_via_gpio(self) -> None:
        # The GPIO routing is encoded by the class — no pin_type / board_number on the subclass.
        config = GlobalGPIOReversionConfig(enabled=True, pin=14, inverted=False)
        assert config.pin_id.pin_type == "GPIO"
        assert config.pin_id.board_number == 1
        assert not hasattr(config, "pin_type")
        assert not hasattr(config, "board_number")
        serialized = config.to_config()
        assert "pin_type" not in serialized
        assert "board_number" not in serialized

    def test_global_i2c_pin_id_uses_configured_expander(self) -> None:
        config = GlobalI2CReversionConfig(enabled=True, pin=5, inverted=False, pin_type="PCF8574", board_number=2)
        assert config.pin_type == "PCF8574"
        assert config.board_number == 2
        assert config.pin_id.pin_type == "PCF8574"
        assert config.pin_id.board_number == 2
        serialized = config.to_config()
        assert serialized["pin_type"] == "PCF8574"
        assert serialized["board_number"] == 2


# --- Helpers for add_discriminator_variant tests ---


class _DummyConfig(ConfigClass):
    """Minimal config class for testing add_discriminator_variant."""

    def __init__(self, kind: str = "Dummy", value: int = 0, **kwargs: Any) -> None:
        self.kind = kind
        self.value = value

    def to_config(self) -> dict[str, Any]:
        return {"kind": self.kind, "value": self.value}


def _make_direct_discriminated(choose: ChooseType) -> DiscriminatedDictType:
    """Build a simple direct (non-list-wrapped) DiscriminatedDictType."""
    return DiscriminatedDictType(
        "kind",
        {
            "Alpha": DictType(
                {"kind": choose, "value": IntType()},
                _DummyConfig,
            ),
        },
        default_variant="Alpha",
    )


def _make_list_wrapped_discriminated(choose: ChooseType) -> ListType:
    """Build a ListType wrapping a DiscriminatedDictType."""
    return ListType(
        _make_direct_discriminated(choose),
        0,
    )


class TestAddDiscriminatorVariantDirect:
    """Tests for add_discriminator_variant on a direct (non-list) DiscriminatedDictType."""

    def test_adds_variant_to_direct_discriminated(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_DIRECT"] = _make_direct_discriminated(choose)
        new_variant = DictType(
            {"kind": choose, "value": IntType(), "extra": StringType()},
            _DummyConfig,
        )
        cfg.add_discriminator_variant("TEST_DIRECT", "Beta", new_variant)
        disc: DiscriminatedDictType = cfg.config_type["TEST_DIRECT"]  # type: ignore[assignment]
        assert "Beta" in disc.variants

    def test_updates_choose_allowed_on_existing_variants(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_DIRECT"] = _make_direct_discriminated(choose)
        new_variant = DictType(
            {"kind": choose, "value": IntType()},
            _DummyConfig,
        )
        cfg.add_discriminator_variant("TEST_DIRECT", "Beta", new_variant)
        assert "Beta" in choose.allowed

    def test_validates_and_deserializes_new_variant(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_DIRECT"] = _make_direct_discriminated(choose)
        new_variant = DictType(
            {"kind": choose, "value": IntType()},
            _DummyConfig,
        )
        cfg.add_discriminator_variant("TEST_DIRECT", "Beta", new_variant)
        disc: DiscriminatedDictType = cfg.config_type["TEST_DIRECT"]  # type: ignore[assignment]
        data = {"kind": "Beta", "value": 42}
        disc.validate("test", data)
        result = disc.from_config(data)
        assert isinstance(result, _DummyConfig)
        assert result.value == 42

    def test_unknown_variant_still_rejected(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_DIRECT"] = _make_direct_discriminated(choose)
        disc: DiscriminatedDictType = cfg.config_type["TEST_DIRECT"]  # type: ignore[assignment]
        with pytest.raises(ConfigError, match="Unknown kind"):
            disc.validate("test", {"kind": "Nonexistent", "value": 0})

    def test_no_op_for_missing_config_name(self) -> None:
        cfg = ConfigManager()
        new_variant = DictType({"kind": ChooseType(allowed=["X"]), "value": IntType()}, _DummyConfig)
        # Should not raise, just warn and return
        cfg.add_discriminator_variant("DOES_NOT_EXIST", "X", new_variant)

    def test_no_op_for_non_discriminated_config(self) -> None:
        cfg = ConfigManager()
        # MAKER_NAME is a StringType, not DiscriminatedDictType
        new_variant = DictType({"kind": ChooseType(allowed=["X"]), "value": IntType()}, _DummyConfig)
        cfg.add_discriminator_variant("MAKER_NAME", "X", new_variant)
        # Should not modify MAKER_NAME
        assert not isinstance(cfg.config_type["MAKER_NAME"], DiscriminatedDictType)


class TestAddDiscriminatorVariantListWrapped:
    """Tests for add_discriminator_variant on a ListType-wrapped DiscriminatedDictType."""

    def test_adds_variant_to_list_wrapped_discriminated(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_LIST"] = _make_list_wrapped_discriminated(choose)
        new_variant = DictType(
            {"kind": choose, "value": IntType(), "extra": FloatType()},
            _DummyConfig,
        )
        cfg.add_discriminator_variant("TEST_LIST", "Beta", new_variant)
        list_type: ListType = cfg.config_type["TEST_LIST"]  # type: ignore[assignment]
        disc: DiscriminatedDictType = list_type.list_type  # type: ignore
        assert "Beta" in disc.variants

    def test_updates_choose_allowed_in_list_wrapped(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_LIST"] = _make_list_wrapped_discriminated(choose)
        new_variant = DictType({"kind": choose, "value": IntType()}, _DummyConfig)
        cfg.add_discriminator_variant("TEST_LIST", "Beta", new_variant)
        assert "Beta" in choose.allowed

    def test_validates_new_variant_in_list_context(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_LIST"] = _make_list_wrapped_discriminated(choose)
        new_variant = DictType({"kind": choose, "value": IntType()}, _DummyConfig)
        cfg.add_discriminator_variant("TEST_LIST", "Beta", new_variant)
        list_type: ListType = cfg.config_type["TEST_LIST"]  # type: ignore[assignment]
        # Validate the whole list with a Beta entry
        list_type.validate("test", [{"kind": "Beta", "value": 99}])

    def test_mixed_variants_in_list(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_LIST"] = _make_list_wrapped_discriminated(choose)
        new_variant = DictType({"kind": choose, "value": IntType()}, _DummyConfig)
        cfg.add_discriminator_variant("TEST_LIST", "Beta", new_variant)
        list_type: ListType = cfg.config_type["TEST_LIST"]  # type: ignore[assignment]
        # Validate a list mixing original and new variant
        mixed = [
            {"kind": "Alpha", "value": 1},
            {"kind": "Beta", "value": 2},
        ]
        list_type.validate("test", mixed)
        results = list_type.from_config(mixed)
        assert len(results) == 2
        assert results[0].kind == "Alpha"
        assert results[1].kind == "Beta"

    def test_does_not_duplicate_allowed_on_repeated_calls(self) -> None:
        cfg = ConfigManager()
        choose = ChooseType(allowed=["Alpha"], default="Alpha")
        cfg.config_type["TEST_LIST"] = _make_list_wrapped_discriminated(choose)
        new_variant = DictType({"kind": choose, "value": IntType()}, _DummyConfig)
        cfg.add_discriminator_variant("TEST_LIST", "Beta", new_variant)
        cfg.add_discriminator_variant("TEST_LIST", "Beta", new_variant)
        assert choose.allowed.count("Beta") == 1
