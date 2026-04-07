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
    DCPumpConfig,
    DictType,
    DiscriminatedDictType,
    FloatType,
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
            "DC": DictType(
                {
                    "pump_type": ChooseOptions.dispenser,
                    "pin_type": ChooseOptions.pin,
                    "board_number": IntType(default=1),
                    "pin": IntType(),
                    "volume_flow": FloatType(),
                    "tube_volume": IntType(),
                },
                DCPumpConfig,
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
    def test_dc_dispatch(self) -> None:
        dt = _build_pump_discriminated_type()
        config_dict = {
            "pump_type": "DC",
            "pin_type": "GPIO",
            "board_number": 1,
            "pin": 14,
            "volume_flow": 30.0,
            "tube_volume": 5,
        }
        dt.validate("test", config_dict)
        result = dt.from_config(config_dict)
        assert isinstance(result, DCPumpConfig)
        assert result.pin == 14
        assert result.volume_flow == pytest.approx(30.0)
        assert result.pump_type == "DC"

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

    def test_dc_round_trip(self) -> None:
        dt = _build_pump_discriminated_type()
        original = DCPumpConfig(pin=14, volume_flow=30.0, tube_volume=5, pin_type="GPIO", board_number=1)
        serialized = dt.to_config(original)
        assert serialized["pump_type"] == "DC"
        assert serialized["pin"] == 14
        restored = dt.from_config(serialized)
        assert isinstance(restored, DCPumpConfig)
        assert restored.pin == original.pin
        assert restored.volume_flow == pytest.approx(original.volume_flow)

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
    def test_dc_is_base(self) -> None:
        dc = DCPumpConfig(pin=14, volume_flow=30.0, tube_volume=5)
        assert isinstance(dc, BasePumpConfig)

    def test_stepper_is_base(self) -> None:
        stepper = StepperPumpConfig(pin=17, dir_pin=27)
        assert isinstance(stepper, BasePumpConfig)

    def test_dc_shared_fields(self) -> None:
        dc = DCPumpConfig(pin=14, volume_flow=30.0, tube_volume=5, pump_type="DC")
        assert dc.pump_type == "DC"
        assert dc.volume_flow == pytest.approx(30.0)
        assert dc.tube_volume == 5

    def test_stepper_shared_fields(self) -> None:
        stepper = StepperPumpConfig(pin=17, dir_pin=27, volume_flow=25.0, tube_volume=3)
        assert stepper.pump_type == "Stepper"
        assert stepper.volume_flow == pytest.approx(25.0)
        assert stepper.tube_volume == 3


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
