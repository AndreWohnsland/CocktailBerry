from pathlib import Path
from unittest.mock import patch

from src.models import AddonData
from src.programs.addons.addons import AddOnManager


def _manager_with_addon(addon_folder: Path) -> AddOnManager:
    (addon_folder / "my_addon.py").write_text("")
    with patch("src.programs.addons.addons.ADDON_FOLDER", addon_folder):
        manager = AddOnManager()
    fake_addon = type("Addon", (), {"__module__": "addons.my_addon"})
    manager.addons["My Addon"] = fake_addon()
    return manager


def test_remove_deletes_the_loaded_addon_file(tmp_path: Path):
    manager = _manager_with_addon(tmp_path)
    with patch("src.programs.addons.addons.ADDON_FOLDER", tmp_path):
        manager.remove_addon(AddonData(name="my addon"))
    assert not (tmp_path / "my_addon.py").exists()
    assert manager.addons == {}


def test_remove_ignores_client_supplied_file_name(tmp_path: Path):
    addon_folder = tmp_path / "addons"
    addon_folder.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("keep me")
    manager = _manager_with_addon(addon_folder)
    with patch("src.programs.addons.addons.ADDON_FOLDER", addon_folder):
        manager.remove_addon(AddonData(name="Unknown", file_name="../victim.txt"))
        manager.remove_addon(AddonData(name="My Addon", file_name="../victim.txt"))
    assert victim.exists()
    assert not (addon_folder / "my_addon.py").exists()
