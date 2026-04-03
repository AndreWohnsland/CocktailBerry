"""Tests for DiscriminatedDictType and polymorphic pump config hierarchy."""

from __future__ import annotations

import pytest

from src.config.config_types import (
    BasePumpConfig,
    ChooseOptions,
    DCPumpConfig,
    DictType,
    DiscriminatedDictType,
    FloatType,
    IntType,
    StepperPumpConfig,
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
