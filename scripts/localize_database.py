"""Localize the working CocktailBerry database to the requested UI language.

Run by the installer after copying ``cocktail_data_en.db`` to the working
``Cocktail_database.db``. Renames Ingredient and Recipe rows in place using
``TRANSLATIONS[lang]``. English (and unknown languages) are no-ops.

Stdlib only: must run before the project's ``uv sync`` step in
``scripts/all_in_one.sh``.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

# Make ``src`` importable when this script is invoked via an absolute path
# (e.g. from the installer in ``scripts/all_in_one.sh``).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.filepath import DATABASE_PATH, DEFAULT_DATABASE_PATH  # noqa: E402

# English -> localized name mappings, keyed by ISO 639-1 language code.
# Add new languages by extending this dict; English keys must match the
# names in ``cocktail_data_en.db``.
TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "en": {"ingredients": {}, "recipes": {}},
    "de": {
        "ingredients": {
            "Dark Rum": "Brauner Rum",
            "White Rum": "Weißer Rum",
            "Orange Juice": "Orangensaft",
            "Pineapple Juice": "Ananassaft",
            "Passion Fruit Juice": "Maracujasaft",
            "Grapefruit Juice": "Grapefruitsaft",
            "Coconut Milk": "Kokosmilch",
            "Raspberry Syrup": "Himbeersirup",
            "Coconut Liqueur": "Kokosnußlikör",
            "Lemon Juice": "Zitronensaft",
            "Grenadine Syrup": "Grenadinesirup",
            "Almond Syrup": "Mandelsirup",
            "Strawberry Liqueur": "Erdbeerlikör",
            "Cranberry Nectar": "Cranberrynektar",
            "Peach Liqueur": "Pfirsischlikör",
            "Lime Juice": "Limettensaft",
            "Water": "Wasser",
        },
        "recipes": {
            "Captain Chaos": "Käptn Chaos",
        },
    },
    "pl": {
        "ingredients": {
            "Dark Rum": "Ciemny rum",
            "White Rum": "Biały rum",
            "Orange Juice": "Sok pomarańczowy",
            "Pineapple Juice": "Sok ananasowy",
            "Passion Fruit Juice": "Sok z marakui",
            "Grapefruit Juice": "Sok grejpfrutowy",
            "Coconut Milk": "Mleko kokosowe",
            "Raspberry Syrup": "Syrop malinowy",
            "Coconut Liqueur": "Likier kokosowy",
            "Lemon Juice": "Sok z cytryny",
            "Grenadine Syrup": "Syrop Grenadynowy",
            "Almond Syrup": "Syrop migdałowy",
            "Strawberry Liqueur": "Likier truskawkowy",
            "Cranberry Nectar": "Nektar żurawinowy",
            "Peach Liqueur": "Likier brzoskwiniowy",
            "Lime Juice": "Sok z limonki",
            "Water": "Woda",
        },
        "recipes": {},
    },
}


def localize_database(language: str, working_db: Path, default_db: Path) -> int:
    """Rename Ingredient and Recipe rows in ``working_db`` to ``language``.

    Returns the number of rows renamed (0 for no-op languages).
    """
    if not working_db.exists():
        if not default_db.exists():
            print(f"Default database not found: {default_db}", file=sys.stderr)
            return -1
        print(f"Working database not found, copying default: {default_db.name} -> {working_db.name}")
        shutil.copy2(default_db, working_db)

    mapping = TRANSLATIONS.get(language)
    if mapping is None:
        print(f"No translations registered for language '{language}', leaving database in English.")
        return 0
    if language == "en":
        print("Language is English, no localization needed.")
        return 0

    renamed = 0
    conn = sqlite3.connect(working_db)
    try:
        cursor = conn.cursor()
        for english, localized in mapping.get("ingredients", {}).items():
            cursor.execute("UPDATE Ingredients SET Name = ? WHERE Name = ?", (localized, english))
            if cursor.rowcount:
                renamed += cursor.rowcount
                print(f"  Ingredient: {english} -> {localized}")
        for english, localized in mapping.get("recipes", {}).items():
            cursor.execute("UPDATE Recipes SET Name = ? WHERE Name = ?", (localized, english))
            if cursor.rowcount:
                renamed += cursor.rowcount
                print(f"  Recipe: {english} -> {localized}")
        conn.commit()
    finally:
        conn.close()

    print(f"Localized {renamed} row(s) to '{language}' in: {working_db}")
    return renamed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Localize the CocktailBerry default database in place.")
    parser.add_argument("language", help="Target language code (e.g. 'en', 'de', 'pl').")
    parser.add_argument(
        "--working-db",
        type=Path,
        default=DATABASE_PATH,
        help="Path to the working DB to rewrite in place (default: Cocktail_database.db at repo root).",
    )
    parser.add_argument(
        "--default-db",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the English default DB used as fallback (default: cocktail_data_en.db at repo root).",
    )
    args = parser.parse_args(argv)
    result = localize_database(args.language, args.working_db, args.default_db)
    return 1 if result < 0 else 0


if __name__ == "__main__":
    sys.exit(main())
