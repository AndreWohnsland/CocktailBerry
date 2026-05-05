from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import ConfigClass, StringType
from src.programs.addons import BaseHardwareExtension
from src.programs.addons.hardware_extensions import HardwareExtensionManager


class DummyConfig(ConfigClass):
    label: str

    def __init__(self, label: str = "default", **kwargs: Any) -> None:
        self.label = label

    def to_config(self) -> dict[str, Any]:
        return {"label": self.label}


class DummyImplementation(BaseHardwareExtension[DummyConfig]):
    def __init__(self) -> None:
        self.cleaned_instances: list[Any] = []

    def create(self, config: DummyConfig) -> Any:
        return {"label": config.label}

    def cleanup(self, instance: Any) -> None:
        self.cleaned_instances.append(instance)


def test_hardware_manager_supports_class_based_implementation(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = HardwareExtensionManager()
    module = SimpleNamespace(
        EXTENSION_NAME="ClassHardware",
        ExtensionConfig=DummyConfig,
        CONFIG_FIELDS={"label": StringType(default="default")},
        Implementation=DummyImplementation,
    )
    monkeypatch.setattr("src.programs.addons.extension_base.import_module", lambda _: module)
    monkeypatch.setattr(cfg, "HW_CLASSHARDWARE", DummyConfig(label="alpha"), raising=False)

    manager._load_extension("class_hardware")

    result = manager.create_all()

    assert result == {"ClassHardware": {"label": "alpha"}}
    implementation = manager.entries["ClassHardware"].implementation
    assert isinstance(implementation, DummyImplementation)

    manager.cleanup_all()

    assert implementation.cleaned_instances == [{"label": "alpha"}]
    assert manager.entries["ClassHardware"].instance is None


def test_hardware_manager_rejects_missing_implementation(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = HardwareExtensionManager()
    module = SimpleNamespace(
        EXTENSION_NAME="Incomplete",
        ExtensionConfig=DummyConfig,
        CONFIG_FIELDS={"label": StringType(default="default")},
    )
    monkeypatch.setattr("src.programs.addons.extension_base.import_module", lambda _: module)

    manager._load_extension("incomplete")

    assert "Incomplete" not in manager.entries
