"""Tests for the producer-blacklist runtime singleton."""

import json
from pathlib import Path

import pytest

from src.programs.blacklist import BlacklistManager


def test_missing_file_loads_as_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_file = tmp_path / "blacklist.json"
    monkeypatch.setattr("src.programs.blacklist.BLACKLIST_FILE", fake_file)
    manager = BlacklistManager()
    assert manager.blacklist.configs == []
    assert manager.blacklisted_tiles() == []
    assert manager.is_config_blacklisted("UI_LANGUAGE") is False
    assert manager.is_tile_blacklisted("cleaning") is False


def test_valid_file_populates_configs_and_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_file = tmp_path / "blacklist.json"
    fake_file.write_text(json.dumps({"configs": ["UI_LANGUAGE", "MAKER_THEME"], "options": ["cleaning", "rfid"]}))
    monkeypatch.setattr("src.programs.blacklist.BLACKLIST_FILE", fake_file)
    manager = BlacklistManager()
    assert sorted(manager.blacklist.configs) == ["MAKER_THEME", "UI_LANGUAGE"]
    assert manager.is_config_blacklisted("UI_LANGUAGE") is True
    assert manager.is_config_blacklisted("UNRELATED") is False
    assert manager.is_tile_blacklisted("cleaning") is True
    assert manager.is_tile_blacklisted("rfid") is True
    assert manager.is_tile_blacklisted("about") is False
    assert sorted(manager.blacklisted_tiles()) == ["cleaning", "rfid"]


def test_malformed_file_falls_back_to_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_file = tmp_path / "blacklist.json"
    fake_file.write_text("{ this is not json")
    monkeypatch.setattr("src.programs.blacklist.BLACKLIST_FILE", fake_file)
    manager = BlacklistManager()
    assert manager.blacklist.configs == []
    assert manager.blacklisted_tiles() == []


def test_reload_picks_up_file_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_file = tmp_path / "blacklist.json"
    monkeypatch.setattr("src.programs.blacklist.BLACKLIST_FILE", fake_file)
    manager = BlacklistManager()
    assert manager.blacklist.configs == []
    fake_file.write_text(json.dumps({"configs": ["MAKER_THEME"], "options": ["about"]}))
    manager.reload()
    assert manager.blacklist.configs == ["MAKER_THEME"]
    assert manager.is_tile_blacklisted("about") is True


def test_unknown_option_field_in_file_is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Forward/backward compat: unknown option keys must not crash startup."""
    fake_file = tmp_path / "blacklist.json"
    fake_file.write_text(json.dumps({"configs": [], "options": ["cleaning", "future_tile_xyz"]}))
    monkeypatch.setattr("src.programs.blacklist.BLACKLIST_FILE", fake_file)
    manager = BlacklistManager()
    # cleaning is recognised; the unknown future_tile_xyz silently disappears.
    assert manager.is_tile_blacklisted("cleaning") is True
    assert manager.is_tile_blacklisted("future_tile_xyz") is False
