"""Tests for `_migrate_normal_led_to_split_variants` (v4.2.0 migration)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from src.migration import migrator


class TestMigrateNormalLedToSplitVariants:
    def test_gpio_entry_migrates_to_normal_over_gpio(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "LED_CONFIG": [
                    {"led_type": "Normal", "pin": 17, "pin_type": "GPIO", "board_number": 1, "default_on": False},
                ],
            },
        )
        migrator._migrate_normal_led_to_split_variants()
        result = read_yaml(config_path)
        assert result["LED_CONFIG"][0]["led_type"] == "Normal over GPIO"
        assert result["LED_CONFIG"][0]["pin"] == 17

    def test_i2c_entry_migrates_to_normal_over_i2c(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "LED_CONFIG": [
                    {"led_type": "Normal", "pin": 5, "pin_type": "MCP23017", "board_number": 2, "default_on": True},
                ],
            },
        )
        migrator._migrate_normal_led_to_split_variants()
        result = read_yaml(config_path)
        assert result["LED_CONFIG"][0]["led_type"] == "Normal over I2C"
        assert result["LED_CONFIG"][0]["pin_type"] == "MCP23017"
        assert result["LED_CONFIG"][0]["board_number"] == 2

    def test_missing_pin_type_defaults_to_gpio(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {"LED_CONFIG": [{"led_type": "Normal", "pin": 10}]},
        )
        migrator._migrate_normal_led_to_split_variants()
        result = read_yaml(config_path)
        assert result["LED_CONFIG"][0]["led_type"] == "Normal over GPIO"

    def test_wsled_entries_untouched(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "LED_CONFIG": [
                    {"led_type": "Normal", "pin": 17, "pin_type": "GPIO", "board_number": 1},
                    {"led_type": "WSLED", "pin": 18, "brightness": 100, "count": 24, "number_rings": 1},
                ],
            },
        )
        migrator._migrate_normal_led_to_split_variants()
        result = read_yaml(config_path)
        assert result["LED_CONFIG"][0]["led_type"] == "Normal over GPIO"
        assert result["LED_CONFIG"][1]["led_type"] == "WSLED"

    def test_already_migrated_entries_untouched(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
        read_yaml: Callable[[Path], dict],
    ) -> None:
        write_yaml(
            config_path,
            {
                "LED_CONFIG": [
                    {"led_type": "Normal over GPIO", "pin": 17},
                    {"led_type": "Normal over I2C", "pin": 5, "pin_type": "PCF8574", "board_number": 1},
                ],
            },
        )
        migrator._migrate_normal_led_to_split_variants()
        result = read_yaml(config_path)
        assert result["LED_CONFIG"][0]["led_type"] == "Normal over GPIO"
        assert result["LED_CONFIG"][1]["led_type"] == "Normal over I2C"

    def test_no_config_file_is_noop(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        missing = tmp_path / "does_not_exist.yaml"
        monkeypatch.setattr(migrator, "CUSTOM_CONFIG_FILE", missing)
        migrator._migrate_normal_led_to_split_variants()
        assert not missing.exists()

    def test_no_changes_does_not_rewrite_file(
        self,
        config_path: Path,
        write_yaml: Callable[[Path, dict], None],
    ) -> None:
        write_yaml(config_path, {"LED_CONFIG": [{"led_type": "WSLED", "pin": 18}]})
        mtime_before = config_path.stat().st_mtime_ns
        migrator._migrate_normal_led_to_split_variants()
        assert config_path.stat().st_mtime_ns == mtime_before
