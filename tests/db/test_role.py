from __future__ import annotations

import pytest

from src.database_commander import (
    DatabaseCommander,
    ElementAlreadyExistsError,
    ElementNotFoundError,
    RoleInUseError,
)


class TestRole:
    def test_create_role_defaults(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        assert role.id is not None
        assert role.name == "manager"
        assert role.privilege_maker is False
        assert role.privilege_options is False
        assert role.tile_permissions == {}

    def test_create_role_with_permissions_and_tiles(self, db_commander: DatabaseCommander):
        role = db_commander.create_role(
            "bartender",
            permissions={"maker": True, "ingredients": True},
            tile_permissions={"cleaning": True, "logs": False},
        )
        assert role.privilege_maker is True
        assert role.privilege_ingredients is True
        assert role.privilege_recipes is False
        assert role.tile_permissions == {"cleaning": True, "logs": False}

    def test_create_role_duplicate_name_raises(self, db_commander: DatabaseCommander):
        db_commander.create_role("manager")
        with pytest.raises(ElementAlreadyExistsError, match="already exists"):
            db_commander.create_role("manager")

    def test_get_all_roles_sorted_by_name(self, db_commander: DatabaseCommander):
        db_commander.create_role("zeta")
        db_commander.create_role("alpha")
        db_commander.create_role("beta")
        roles = db_commander.get_all_roles()
        assert [r.name for r in roles] == ["alpha", "beta", "zeta"]

    def test_get_role_by_id(self, db_commander: DatabaseCommander):
        created = db_commander.create_role("manager")
        fetched = db_commander.get_role_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "manager"

    def test_get_role_by_name(self, db_commander: DatabaseCommander):
        db_commander.create_role("manager")
        fetched = db_commander.get_role_by_name("manager")
        assert fetched is not None
        assert fetched.name == "manager"

    def test_update_role_name(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        updated = db_commander.update_role(role.id, name="senior_manager")
        assert updated.name == "senior_manager"

    def test_update_role_rename_does_not_unbind_waiters(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        db_commander.create_waiter("nfc_001", "Alice", role_id=role.id)
        db_commander.update_role(role.id, name="senior_manager")
        waiter = db_commander.get_waiter_by_nfc_id("nfc_001")
        assert waiter is not None
        assert waiter.role_id == role.id
        assert waiter.role.name == "senior_manager"

    def test_update_role_duplicate_name_raises(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        db_commander.create_role("admin")
        with pytest.raises(ElementAlreadyExistsError, match="already exists"):
            db_commander.update_role(role.id, name="admin")

    def test_update_role_permissions(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        updated = db_commander.update_role(role.id, permissions={"options": True, "bottles": True})
        assert updated.privilege_options is True
        assert updated.privilege_bottles is True
        assert updated.privilege_maker is False

    def test_update_role_tile_permissions(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        updated = db_commander.update_role(role.id, tile_permissions={"cleaning": True})
        assert updated.tile_permissions == {"cleaning": True}

    def test_update_role_not_found_raises(self, db_commander: DatabaseCommander):
        with pytest.raises(ElementNotFoundError, match="not found"):
            db_commander.update_role(999, name="x")

    def test_delete_role(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        db_commander.delete_role(role.id)
        assert db_commander.get_role_by_id(role.id) is None

    def test_delete_role_in_use_raises(self, db_commander: DatabaseCommander):
        role = db_commander.create_role("manager")
        db_commander.create_waiter("nfc_001", "Alice", role_id=role.id)
        with pytest.raises(RoleInUseError):
            db_commander.delete_role(role.id)
        # role still present, waiter still bound
        assert db_commander.get_role_by_id(role.id) is not None

    def test_delete_role_not_found_raises(self, db_commander: DatabaseCommander):
        with pytest.raises(ElementNotFoundError, match="not found"):
            db_commander.delete_role(999)

    def test_tile_permissions_json_round_trip(self, db_commander: DatabaseCommander):
        tiles = {"cleaning": True, "configuration": False, "logs": True}
        role = db_commander.create_role("manager", tile_permissions=tiles)
        fetched = db_commander.get_role_by_id(role.id)
        assert fetched is not None
        assert fetched.tile_permissions == tiles
