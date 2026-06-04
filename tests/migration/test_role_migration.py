"""Golden migration test for waiter privilege → roles transition (v4.0.0)."""

from __future__ import annotations

import contextlib
import json
import sqlite3
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from src.migration import update_data
from src.models import OptionTiles


@pytest.fixture
def v3_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Path, Any, Any]:
    """Build a temp v3-shaped DB with Waiters (5 priv columns) + WaiterLog rows. No Roles table."""
    db_path = tmp_path / "v3.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    monkeypatch.setattr(update_data, "DATABASE_PATH", db_path)
    monkeypatch.setattr(update_data, "DEFAULT_DATABASE_PATH", db_path)
    monkeypatch.setattr(update_data, "BACKUP_FOLDER", backup_dir)

    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE Waiters (
                NFC_ID TEXT PRIMARY KEY NOT NULL,
                Name TEXT NOT NULL UNIQUE,
                Privilege_Maker BOOLEAN NOT NULL DEFAULT 0,
                Privilege_Ingredients BOOLEAN NOT NULL DEFAULT 0,
                Privilege_Recipes BOOLEAN NOT NULL DEFAULT 0,
                Privilege_Bottles BOOLEAN NOT NULL DEFAULT 0,
                Privilege_Options BOOLEAN NOT NULL DEFAULT 0
            );
            CREATE TABLE Recipes (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE WaiterLog (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp TEXT NOT NULL,
                Waiter_NFC_ID TEXT,
                Recipe_ID INTEGER,
                Volume INTEGER NOT NULL,
                Is_Virgin BOOLEAN NOT NULL,
                FOREIGN KEY (Waiter_NFC_ID) REFERENCES Waiters(NFC_ID) ON DELETE SET NULL,
                FOREIGN KEY (Recipe_ID) REFERENCES Recipes(ID) ON DELETE SET NULL
            );
            """
        )
        cur.executemany(
            "INSERT INTO Waiters (NFC_ID, Name, Privilege_Maker, Privilege_Ingredients, "
            "Privilege_Recipes, Privilege_Bottles, Privilege_Options) VALUES (?, ?, ?, ?, ?, ?, ?);",
            [
                # full options — promoted to admin role
                ("nfc_001", "Alice", 1, 1, 1, 1, 1),
                # maker only (no options) — preserves perms exactly
                ("nfc_002", "Bob", 1, 0, 0, 0, 0),
                ("nfc_003", "Charlie", 1, 0, 0, 0, 0),
                # ingredients + recipes (no options)
                ("nfc_004", "Dora", 0, 1, 1, 0, 0),
                # full options dup — same admin role as Alice
                ("nfc_005", "Eve", 1, 1, 1, 1, 1),
                # options-only — also promoted to admin role (same as Alice/Eve)
                ("nfc_006", "Frank", 0, 0, 0, 0, 1),
            ],
        )
        cur.execute("INSERT INTO Recipes (Name) VALUES ('Test Cocktail');")
        cur.executemany(
            "INSERT INTO WaiterLog (Timestamp, Waiter_NFC_ID, Recipe_ID, Volume, Is_Virgin) VALUES (?, ?, ?, ?, ?);",
            [
                ("2025-01-01 10:00:00", "nfc_001", 1, 250, 0),
                ("2025-01-01 11:00:00", "nfc_002", 1, 300, 0),
                ("2025-01-01 12:00:00", "nfc_004", 1, 200, 1),
            ],
        )
        conn.commit()

    yield db_path


def _columns(db_path: Path, table: str) -> list[str]:
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table});")
        return [row[1] for row in cur.fetchall()]


def _query(db_path: Path, sql: str, params: tuple = ()) -> list[tuple]:
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return list(cur.fetchall())


class TestRoleMigration:
    def test_creates_roles_for_each_unique_privilege_tuple(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        roles = _query(v3_database, "SELECT Name, Privilege_Options, Tile_Permissions FROM Roles ORDER BY ID;")
        # 3 distinct effective tuples after admin-promotion of any options=True waiter:
        # admin (Alice/Eve/Frank), maker-only (Bob/Charlie), ing+rec (Dora)
        assert len(roles) == 3
        names = [r[0] for r in roles]
        assert names == ["role_1", "role_2", "role_3"]

    def test_assigns_role_id_to_every_waiter(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        rows = _query(v3_database, "SELECT NFC_ID, Role_ID FROM Waiters ORDER BY NFC_ID;")
        assert len(rows) == 6
        for nfc_id, role_id in rows:
            assert role_id is not None, f"Waiter {nfc_id} has NULL Role_ID"

    def test_options_waiters_collapse_into_single_admin_role(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        # Alice (full options), Eve (full options), Frank (options-only) all promoted to the same admin role.
        alice_role = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_001';")[0][0]
        eve_role = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_005';")[0][0]
        frank_role = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_006';")[0][0]
        assert alice_role == eve_role == frank_role

    def test_groups_duplicate_privilege_tuples_into_same_role(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        bob_role = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_002';")[0][0]
        charlie_role = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_003';")[0][0]
        dora_role = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_004';")[0][0]
        assert bob_role == charlie_role
        assert bob_role != dora_role

    def test_admin_role_has_full_tab_and_tile_permissions(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        role_id = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_001';")[0][0]
        cols = _query(
            v3_database,
            "SELECT Privilege_Maker, Privilege_Ingredients, Privilege_Recipes, "
            "Privilege_Bottles, Privilege_Options, Tile_Permissions FROM Roles WHERE ID=?;",
            (role_id,),
        )[0]
        # Tab perms all True
        assert all(bool(v) for v in cols[:5])
        # Tile perms all True
        tiles = json.loads(cols[5])
        assert all(v is True for v in tiles.values())
        assert set(tiles.keys()) == set(OptionTiles.model_fields.keys())

    def test_options_only_waiter_gains_all_tab_perms(self, v3_database: Path):
        # Frank originally had only Privilege_Options=True → becomes full admin
        update_data.migrate_waiter_privileges_to_roles()
        role_id = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_006';")[0][0]
        cols = _query(
            v3_database,
            "SELECT Privilege_Maker, Privilege_Ingredients, Privilege_Recipes, "
            "Privilege_Bottles, Privilege_Options FROM Roles WHERE ID=?;",
            (role_id,),
        )[0]
        assert all(bool(v) for v in cols)

    def test_tile_permissions_all_false_for_no_options_role(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        role_id = _query(v3_database, "SELECT Role_ID FROM Waiters WHERE NFC_ID='nfc_002';")[0][0]
        tiles_json = _query(v3_database, "SELECT Tile_Permissions FROM Roles WHERE ID=?;", (role_id,))[0][0]
        tiles = json.loads(tiles_json)
        assert all(v is False for v in tiles.values())

    def test_drops_privilege_columns(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        cols = _columns(v3_database, "Waiters")
        assert "Privilege_Maker" not in cols
        assert "Privilege_Options" not in cols
        assert "Role_ID" in cols

    def test_preserves_waiter_logs(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        logs = _query(v3_database, "SELECT Waiter_NFC_ID, Volume, Is_Virgin FROM WaiterLog ORDER BY ID;")
        assert len(logs) == 3
        assert logs[0] == ("nfc_001", 250, 0)
        assert logs[1] == ("nfc_002", 300, 0)
        assert logs[2] == ("nfc_004", 200, 1)

    def test_idempotent_re_run(self, v3_database: Path):
        update_data.migrate_waiter_privileges_to_roles()
        roles_before = _query(v3_database, "SELECT COUNT(*) FROM Roles;")[0][0]
        # Second run should be a no-op
        update_data.migrate_waiter_privileges_to_roles()
        roles_after = _query(v3_database, "SELECT COUNT(*) FROM Roles;")[0][0]
        assert roles_before == roles_after

    def test_seeds_default_role_when_no_waiters(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        db_path = tmp_path / "empty.db"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        monkeypatch.setattr(update_data, "DATABASE_PATH", db_path)
        monkeypatch.setattr(update_data, "DEFAULT_DATABASE_PATH", db_path)
        monkeypatch.setattr(update_data, "BACKUP_FOLDER", backup_dir)
        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "CREATE TABLE Waiters (NFC_ID TEXT PRIMARY KEY, Name TEXT, "
                "Privilege_Maker BOOLEAN, Privilege_Ingredients BOOLEAN, "
                "Privilege_Recipes BOOLEAN, Privilege_Bottles BOOLEAN, Privilege_Options BOOLEAN);"
            )
            conn.commit()
        update_data.migrate_waiter_privileges_to_roles()
        roles = _query(db_path, "SELECT Name FROM Roles;")
        assert roles == [("default",)]
