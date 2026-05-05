from __future__ import annotations

import pytest

from src.database_commander import DatabaseCommander, ElementAlreadyExistsError, ElementNotFoundError


def _create_default_role(db_commander: DatabaseCommander, name: str = "default") -> int:
    """Create a baseline role and return its id (every waiter needs one)."""
    role = db_commander.create_role(name)
    return role.id


class TestWaiter:
    def test_create_waiter(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        waiter = db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        assert waiter.nfc_id == "nfc_001"
        assert waiter.name == "Alice"
        assert waiter.role_id == role_id
        assert waiter.role.name == "default"

    def test_create_waiter_unknown_role_raises(self, db_commander: DatabaseCommander):
        with pytest.raises(ElementNotFoundError, match="not found"):
            db_commander.create_waiter("nfc_001", "Alice", role_id=999)

    def test_create_waiter_duplicate_name_raises(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        with pytest.raises(ElementAlreadyExistsError, match="already exists"):
            db_commander.create_waiter("nfc_002", "Alice", role_id=role_id)

    def test_create_waiter_duplicate_nfc_id_raises(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        with pytest.raises(ElementAlreadyExistsError, match="already exists"):
            db_commander.create_waiter("nfc_001", "Bob", role_id=role_id)

    def test_get_all_waiters_empty(self, db_commander: DatabaseCommander):
        waiters = db_commander.get_all_waiters()
        assert waiters == []

    def test_get_all_waiters_returns_sorted_by_name(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_003", "Charlie", role_id=role_id)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.create_waiter("nfc_002", "Bob", role_id=role_id)
        waiters = db_commander.get_all_waiters()
        assert len(waiters) == 3
        assert [w.name for w in waiters] == ["Alice", "Bob", "Charlie"]

    def test_get_waiter_by_nfc_id(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        waiter = db_commander.get_waiter_by_nfc_id("nfc_001")
        assert waiter is not None
        assert waiter.name == "Alice"
        assert waiter.role.id == role_id

    def test_get_waiter_by_nfc_id_not_found(self, db_commander: DatabaseCommander):
        waiter = db_commander.get_waiter_by_nfc_id("nonexistent")
        assert waiter is None

    def test_update_waiter_name(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        updated = db_commander.update_waiter("nfc_001", name="Alice Updated")
        assert updated.name == "Alice Updated"
        assert updated.nfc_id == "nfc_001"
        fetched = db_commander.get_waiter_by_nfc_id("nfc_001")
        assert fetched is not None
        assert fetched.name == "Alice Updated"

    def test_update_waiter_role(self, db_commander: DatabaseCommander):
        role_a = _create_default_role(db_commander, "role_a")
        role_b = _create_default_role(db_commander, "role_b")
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_a)
        updated = db_commander.update_waiter("nfc_001", role_id=role_b)
        assert updated.role_id == role_b
        assert updated.role.name == "role_b"

    def test_update_waiter_unknown_role_raises(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        with pytest.raises(ElementNotFoundError, match="not found"):
            db_commander.update_waiter("nfc_001", role_id=999)

    def test_update_waiter_not_found_raises(self, db_commander: DatabaseCommander):
        with pytest.raises(ElementNotFoundError, match="not found"):
            db_commander.update_waiter("nonexistent", name="Name")

    def test_update_waiter_duplicate_name_raises(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.create_waiter("nfc_002", "Bob", role_id=role_id)
        with pytest.raises(ElementAlreadyExistsError, match="already exists"):
            db_commander.update_waiter("nfc_002", name="Alice")

    def test_update_waiter_same_name_allowed(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        updated = db_commander.update_waiter("nfc_001", name="Alice")
        assert updated.name == "Alice"

    def test_delete_waiter(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.delete_waiter("nfc_001")
        assert db_commander.get_waiter_by_nfc_id("nfc_001") is None
        assert db_commander.get_all_waiters() == []

    def test_delete_waiter_not_found_raises(self, db_commander: DatabaseCommander):
        with pytest.raises(ElementNotFoundError, match="not found"):
            db_commander.delete_waiter("nonexistent")

    def test_delete_waiter_nullifies_logs(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 300, False)
        db_commander.log_waiter_cocktail("nfc_001", 2, 250, True)
        assert len(db_commander.get_waiter_logs()) == 2
        db_commander.delete_waiter("nfc_001")
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 2
        for log in logs:
            assert log.waiter_nfc_id is None
            assert log.waiter is None

    def test_log_waiter_cocktail(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 300, False)
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 1
        log = logs[0]
        assert log.waiter_nfc_id == "nfc_001"
        assert log.recipe_id == 1
        assert log.volume == 300
        assert log.is_virgin is False
        assert log.timestamp is not None

    def test_log_waiter_cocktail_relationships_eagerly_loaded(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 300, False)
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 1
        first_log = logs[0]
        assert first_log.waiter is not None
        assert first_log.recipe is not None
        assert first_log.waiter.name == "Alice"
        assert first_log.recipe.name == "Cuba Libre"

    def test_log_waiter_cocktail_relationship_none_recipe(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", None, 200, False)  # type: ignore
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 1
        assert logs[0].waiter.name == "Alice"  # type: ignore
        assert logs[0].recipe is None

    def test_log_waiter_cocktail_virgin(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 250, True)
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 1
        assert logs[0].is_virgin is True

    def test_get_waiter_logs_empty(self, db_commander: DatabaseCommander):
        logs = db_commander.get_waiter_logs()
        assert logs == []

    def test_get_waiter_logs_ordered_by_timestamp_desc(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 300, False)
        db_commander.log_waiter_cocktail("nfc_001", 2, 250, True)
        db_commander.log_waiter_cocktail("nfc_001", 1, 200, False)
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 3
        for i in range(len(logs) - 1):
            assert logs[i].timestamp >= logs[i + 1].timestamp

    def test_get_waiter_logs_multiple_waiters(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.create_waiter("nfc_002", "Bob", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 300, False)
        db_commander.log_waiter_cocktail("nfc_002", 2, 250, True)
        db_commander.log_waiter_cocktail("nfc_001", 1, 200, False)
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 3
        alice_logs = [log for log in logs if log.waiter_nfc_id == "nfc_001"]
        bob_logs = [log for log in logs if log.waiter_nfc_id == "nfc_002"]
        assert len(alice_logs) == 2
        assert len(bob_logs) == 1

    def test_multiple_create_and_delete(self, db_commander: DatabaseCommander):
        role_id = _create_default_role(db_commander)
        db_commander.create_waiter("nfc_001", "Alice", role_id=role_id)
        db_commander.create_waiter("nfc_002", "Bob", role_id=role_id)
        db_commander.create_waiter("nfc_003", "Charlie", role_id=role_id)
        db_commander.log_waiter_cocktail("nfc_001", 1, 300, False)
        db_commander.log_waiter_cocktail("nfc_002", 2, 250, True)
        db_commander.delete_waiter("nfc_001")
        waiters = db_commander.get_all_waiters()
        assert len(waiters) == 2
        assert {w.name for w in waiters} == {"Bob", "Charlie"}
        logs = db_commander.get_waiter_logs()
        assert len(logs) == 2
        alice_logs = [log for log in logs if log.waiter_nfc_id is None]
        bob_logs = [log for log in logs if log.waiter_nfc_id == "nfc_002"]
        assert len(alice_logs) == 1
        assert len(bob_logs) == 1
