"""Tests for `_migrate_dc_pump_to_split_variants` (v4.2.0 migration)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.migration import migrator


def _write_yaml(path: Path, data: dict) -> None:
    with path.open("w", encoding="UTF-8") as stream:
        yaml.dump(data, stream, default_flow_style=False)


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="UTF-8") as stream:
        return yaml.safe_load(stream)


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "custom_config.yaml"
    monkeypatch.setattr(migrator, "CUSTOM_CONFIG_FILE", path)
    return path


class TestMigrateDcPumpToSplitVariants:
    def test_gpio_entry_migrates_to_dc_over_gpio(self, config_path: Path) -> None:
        _write_yaml(
            config_path,
            {
                "PUMP_CONFIG": [
                    {"pump_type": "DC", "pin": 14, "pin_type": "GPIO", "board_number": 1, "volume_flow": 30.0},
                ],
            },
        )
        migrator._migrate_dc_pump_to_split_variants()
        result = _read_yaml(config_path)
        assert result["PUMP_CONFIG"][0]["pump_type"] == "DC over GPIO"
        # other fields are preserved
        assert result["PUMP_CONFIG"][0]["pin"] == 14
        assert result["PUMP_CONFIG"][0]["pin_type"] == "GPIO"

    def test_i2c_entry_migrates_to_dc_over_i2c(self, config_path: Path) -> None:
        _write_yaml(
            config_path,
            {
                "PUMP_CONFIG": [
                    {"pump_type": "DC", "pin": 5, "pin_type": "MCP23017", "board_number": 2, "volume_flow": 30.0},
                ],
            },
        )
        migrator._migrate_dc_pump_to_split_variants()
        result = _read_yaml(config_path)
        assert result["PUMP_CONFIG"][0]["pump_type"] == "DC over I2C"
        assert result["PUMP_CONFIG"][0]["pin_type"] == "MCP23017"
        assert result["PUMP_CONFIG"][0]["board_number"] == 2

    def test_missing_pin_type_defaults_to_gpio(self, config_path: Path) -> None:
        _write_yaml(
            config_path,
            {"PUMP_CONFIG": [{"pump_type": "DC", "pin": 10, "volume_flow": 30.0}]},
        )
        migrator._migrate_dc_pump_to_split_variants()
        result = _read_yaml(config_path)
        assert result["PUMP_CONFIG"][0]["pump_type"] == "DC over GPIO"

    def test_already_migrated_entries_untouched(self, config_path: Path) -> None:
        _write_yaml(
            config_path,
            {
                "PUMP_CONFIG": [
                    {"pump_type": "DC over GPIO", "pin": 14},
                    {"pump_type": "DC over I2C", "pin": 5, "pin_type": "PCF8574", "board_number": 1},
                ],
            },
        )
        migrator._migrate_dc_pump_to_split_variants()
        result = _read_yaml(config_path)
        assert result["PUMP_CONFIG"][0]["pump_type"] == "DC over GPIO"
        assert result["PUMP_CONFIG"][1]["pump_type"] == "DC over I2C"

    def test_stepper_entries_untouched(self, config_path: Path) -> None:
        _write_yaml(
            config_path,
            {
                "PUMP_CONFIG": [
                    {"pump_type": "DC", "pin": 14, "pin_type": "GPIO", "board_number": 1},
                    {"pump_type": "Stepper", "pin": 17, "dir_pin": 27, "driver_type": "A4988"},
                ],
            },
        )
        migrator._migrate_dc_pump_to_split_variants()
        result = _read_yaml(config_path)
        assert result["PUMP_CONFIG"][0]["pump_type"] == "DC over GPIO"
        assert result["PUMP_CONFIG"][1]["pump_type"] == "Stepper"

    def test_no_config_file_is_noop(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        missing = tmp_path / "does_not_exist.yaml"
        monkeypatch.setattr(migrator, "CUSTOM_CONFIG_FILE", missing)
        # Should not raise even when the file is missing
        migrator._migrate_dc_pump_to_split_variants()
        assert not missing.exists()

    def test_no_changes_does_not_rewrite_file(self, config_path: Path) -> None:
        original = {"PUMP_CONFIG": [{"pump_type": "Stepper", "pin": 17, "dir_pin": 27}]}
        _write_yaml(config_path, original)
        mtime_before = config_path.stat().st_mtime_ns
        migrator._migrate_dc_pump_to_split_variants()
        assert config_path.stat().st_mtime_ns == mtime_before
