"""Script to create an English version of the default cocktail database.

Copies Cocktail_database_default.db to Cocktail_database_default_en.db
and translates ingredient names and recipe names from German to English.
"""

import shutil
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).parent.parent
SOURCE_DB = DB_DIR / "cocktail_data.db"
TARGET_DB = DB_DIR / "cocktail_data_en.db"

# German -> English ingredient name mapping
INGREDIENT_TRANSLATIONS: dict[str, str] = {
    "Brauner Rum": "Dark Rum",
    "Weißer Rum": "White Rum",
    "Orangensaft": "Orange Juice",
    "Ananassaft": "Pineapple Juice",
    "Maracujasaft": "Passion Fruit Juice",
    "Grapefruitsaft": "Grapefruit Juice",
    "Kokosmilch": "Coconut Milk",
    "Himbeersirup": "Raspberry Syrup",
    "Kokosnußlikör": "Coconut Liqueur",
    "Zitronensaft": "Lemon Juice",
    "Grenadinesirup": "Grenadine Syrup",
    "Mandelsirup": "Almond Syrup",
    "Erdbeerlikör": "Strawberry Liqueur",
    "Cranberrynektar": "Cranberry Nectar",
    "Pfirsischlikör": "Peach Liqueur",
    "Limettensaft": "Lime Juice",
    "Wasser": "Water",
}

# German -> English recipe name mapping (only non-English names)
RECIPE_TRANSLATIONS: dict[str, str] = {
    "Käptn Chaos": "Captain Chaos",
}


def create_english_db() -> None:
    """Copy the default DB and translate all names to English."""
    if not SOURCE_DB.exists():
        print(f"Source database not found: {SOURCE_DB}")
        return

    # Copy the database file
    shutil.copy2(SOURCE_DB, TARGET_DB)
    print(f"Copied {SOURCE_DB.name} -> {TARGET_DB.name}")

    conn = sqlite3.connect(TARGET_DB)
    cursor = conn.cursor()

    # Translate ingredient names
    for german, english in INGREDIENT_TRANSLATIONS.items():
        cursor.execute("UPDATE Ingredients SET Name = ? WHERE Name = ?", (english, german))
        if cursor.rowcount:
            print(f"  Ingredient: {german} -> {english}")

    # Translate recipe names
    for german, english in RECIPE_TRANSLATIONS.items():
        cursor.execute("UPDATE Recipes SET Name = ? WHERE Name = ?", (english, german))
        if cursor.rowcount:
            print(f"  Recipe: {german} -> {english}")

    conn.commit()
    conn.close()
    print(f"\nDone. English database saved to: {TARGET_DB}")


if __name__ == "__main__":
    create_english_db()
