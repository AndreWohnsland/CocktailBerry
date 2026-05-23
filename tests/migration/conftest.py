"""Shared fixtures for migrator tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from src.migration import migrator


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "custom_config.yaml"
    monkeypatch.setattr(migrator, "CUSTOM_CONFIG_FILE", path)
    return path


@pytest.fixture
def write_yaml() -> Callable[[Path, dict], None]:
    def _write(path: Path, data: dict) -> None:
        with path.open("w", encoding="UTF-8") as stream:
            yaml.dump(data, stream, default_flow_style=False)

    return _write


@pytest.fixture
def read_yaml() -> Callable[[Path], dict]:
    def _read(path: Path) -> dict:
        with path.open(encoding="UTF-8") as stream:
            return yaml.safe_load(stream)

    return _read
