"""Tests for `_migrate_global_reversion_to_split_variants` (v4.2.0 migration)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from src.migration import migrator


class TestMigrateGlobalReversionToSplitVariants:
    def test_gpio_entry_migrates_to_global_over_gpio(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "MAKER_PUMP_REVERSION_CONFIG": {
                    "reversion_type": "Global",
                    "enabled": True,
                    "pin": 14,
                    "pin_type": "GPIO",
                    "board_number": 1,
                    "inverted": False,
                },
            },
        )
        migrator._migrate_global_reversion_to_split_variants()
        result = read_yaml(config_path)
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["reversion_type"] == "Global over GPIO"
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["pin"] == 14

    def test_i2c_entry_migrates_to_global_over_i2c(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "MAKER_PUMP_REVERSION_CONFIG": {
                    "reversion_type": "Global",
                    "enabled": True,
                    "pin": 5,
                    "pin_type": "PCF8574",
                    "board_number": 2,
                    "inverted": False,
                },
            },
        )
        migrator._migrate_global_reversion_to_split_variants()
        result = read_yaml(config_path)
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["reversion_type"] == "Global over I2C"
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["pin_type"] == "PCF8574"
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["board_number"] == 2

    def test_missing_pin_type_defaults_to_gpio(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {"MAKER_PUMP_REVERSION_CONFIG": {"reversion_type": "Global", "enabled": False, "pin": 0}},
        )
        migrator._migrate_global_reversion_to_split_variants()
        result = read_yaml(config_path)
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["reversion_type"] == "Global over GPIO"

    def test_dispenser_controlled_untouched(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {"MAKER_PUMP_REVERSION_CONFIG": {"reversion_type": "Dispenser Controlled", "enabled": True}},
        )
        migrator._migrate_global_reversion_to_split_variants()
        result = read_yaml(config_path)
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["reversion_type"] == "Dispenser Controlled"

    def test_already_migrated_untouched(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "MAKER_PUMP_REVERSION_CONFIG": {
                    "reversion_type": "Global over I2C",
                    "enabled": True,
                    "pin": 5,
                    "pin_type": "PCF8574",
                    "board_number": 2,
                    "inverted": False,
                },
            },
        )
        migrator._migrate_global_reversion_to_split_variants()
        result = read_yaml(config_path)
        assert result["MAKER_PUMP_REVERSION_CONFIG"]["reversion_type"] == "Global over I2C"

    def test_no_config_file_is_noop(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        missing = tmp_path / "does_not_exist.yaml"
        monkeypatch.setattr(migrator, "CUSTOM_CONFIG_FILE", missing)
        migrator._migrate_global_reversion_to_split_variants()
        assert not missing.exists()
