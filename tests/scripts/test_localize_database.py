"""Tests for ``scripts/localize_database.py``.

Lives in ``tests/scripts/`` to keep installer/script-level tests separate
from main application tests.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEFAULT_DB = REPO_ROOT / "cocktail_data_en.db"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import localize_database  # noqa: E402  # ty:ignore[unresolved-import]


def _ingredient_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {row[0] for row in conn.execute("SELECT Name FROM Ingredients")}
    finally:
        conn.close()


def _recipe_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {row[0] for row in conn.execute("SELECT Name FROM Recipes")}
    finally:
        conn.close()


@pytest.fixture
def working_db(tmp_path: Path) -> Path:
    """Fresh copy of the English default DB at a tmp working path."""
    if not DEFAULT_DB.exists():
        pytest.skip(f"English default DB not found at {DEFAULT_DB}")
    target = tmp_path / "Cocktail_database.db"
    shutil.copy2(DEFAULT_DB, target)
    return target


def test_english_is_noop(working_db: Path) -> None:
    before = _ingredient_names(working_db)
    renamed = localize_database.localize_database("en", working_db, DEFAULT_DB)
    assert renamed == 0
    assert _ingredient_names(working_db) == before


def test_de_renames_ingredients_and_recipes(working_db: Path) -> None:
    renamed = localize_database.localize_database("de", working_db, DEFAULT_DB)
    assert renamed > 0
    ingredients = _ingredient_names(working_db)
    assert "Brauner Rum" in ingredients
    assert "Weißer Rum" in ingredients
    assert "Dark Rum" not in ingredients
    recipes = _recipe_names(working_db)
    assert "Käptn Chaos" in recipes
    assert "Captain Chaos" not in recipes


def test_pl_renames_ingredients_only(working_db: Path) -> None:
    recipes_before = _recipe_names(working_db)
    renamed = localize_database.localize_database("pl", working_db, DEFAULT_DB)
    assert renamed > 0
    ingredients = _ingredient_names(working_db)
    assert "Ciemny rum" in ingredients
    assert "Biały rum" in ingredients
    assert "Dark Rum" not in ingredients
    assert _recipe_names(working_db) == recipes_before


def test_unknown_language_is_noop(working_db: Path) -> None:
    before = _ingredient_names(working_db)
    renamed = localize_database.localize_database("xx", working_db, DEFAULT_DB)
    assert renamed == 0
    assert _ingredient_names(working_db) == before


def test_missing_working_db_falls_back_to_english(tmp_path: Path) -> None:
    if not DEFAULT_DB.exists():
        pytest.skip(f"English default DB not found at {DEFAULT_DB}")
    working = tmp_path / "Cocktail_database.db"
    assert not working.exists()
    renamed = localize_database.localize_database("de", working, DEFAULT_DB)
    assert working.exists()
    assert renamed > 0
    assert "Brauner Rum" in _ingredient_names(working)


def test_missing_default_db_returns_failure(tmp_path: Path) -> None:
    missing_default = tmp_path / "does_not_exist.db"
    missing_working = tmp_path / "Cocktail_database.db"
    assert localize_database.localize_database("de", missing_working, missing_default) == -1


def test_main_cli_invokes_localize(tmp_path: Path) -> None:
    if not DEFAULT_DB.exists():
        pytest.skip(f"English default DB not found at {DEFAULT_DB}")
    working = tmp_path / "Cocktail_database.db"
    shutil.copy2(DEFAULT_DB, working)
    rc = localize_database.main(
        ["de", "--working-db", str(working), "--default-db", str(DEFAULT_DB)],
    )
    assert rc == 0
    assert "Brauner Rum" in _ingredient_names(working)
