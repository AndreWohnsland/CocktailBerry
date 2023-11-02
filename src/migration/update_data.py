from typing import Dict, List
from sqlite3 import OperationalError

from src.logger_handler import LoggerHandler
from src.models import Cocktail, Ingredient
from src.database_commander import DatabaseCommander, DatabaseHandler

_logger = LoggerHandler("update_data_module")


def add_new_recipes_from_default_db():
    """Adds the new recipes since the initial creation of the db"""
    new_names = [
        "Beachbum",
        "Bay Breeze",
        "Belladonna",
        "Black-Eyed Susan",
        "Blue Hawaii",
        "Blue Ricardo",
        "Flamingo",
        "Orange Crush",
        "Bocce Ball",
        "Fuzzy Navel",
        "Madras",
        "Woo Woo",
        "Vodka Tonic",
        "Sidewinder’s Fang",
        "212",
        "Cantarito",
        "Paloma",
    ]
    _logger.log_event("INFO", "Adding new recipes from default db, if any are missing.")
    _add_new_recipes_from_list(new_names)


def _add_new_recipes_from_list(new_names: List[str]):
    """Adds the new recipes from the given list"""
    # build connection to provided and local db
    # gets the new recipe data, check whats missing and insert it
    default_db = DatabaseCommander(use_default=True)
    local_db = DatabaseCommander()
    local_db.create_backup()
    cocktails_to_add = _get_new_cocktails(new_names, default_db, local_db)
    ingredient_to_add = _get_new_ingredients(local_db, cocktails_to_add)
    _insert_new_ingredients(default_db, local_db, ingredient_to_add)
    _insert_new_recipes(local_db, cocktails_to_add)


def _insert_new_recipes(local_db: DatabaseCommander, cocktails_to_add: List[Cocktail]):
    """Inserts the data for the new recipes into the db"""
    all_ingredients = local_db.get_all_ingredients()
    ing_mapping: Dict[str, Ingredient] = {}
    for ing in all_ingredients:
        ing_mapping[ing.name] = ing
    _logger.log_event("INFO", f"Adding recipes: {[c.name for c in cocktails_to_add]}")
    for rec in cocktails_to_add:
        local_db.insert_new_recipe(
            rec.name, rec.alcohol, rec.amount,
            rec.enabled, rec.virgin_available
        )
        new_cocktail = local_db.get_cocktail(rec.name)
        if new_cocktail is None:
            continue
        for ing in rec.ingredients:
            ing_data = ing_mapping[ing.name]
            local_db.insert_recipe_data(new_cocktail.id, ing_data.id, ing.amount)


def _insert_new_ingredients(default_db: DatabaseCommander, local_db: DatabaseCommander, ingredient_to_add: List[str]):
    """Gets and inserts the given ingredients into the local db"""
    _logger.log_event("INFO", f"Adding ingredients: {ingredient_to_add}")
    for ingredient in ingredient_to_add:
        ing = default_db.get_ingredient(ingredient)
        if ing is None:
            continue
        local_db.insert_new_ingredient(
            ing.name, ing.alcohol, ing.bottle_volume, bool(ing.hand), bool(ing.slow), ing.cost
        )


def _get_new_ingredients(local_db: DatabaseCommander, cocktails_to_add: List[Cocktail]) -> List[str]:
    """Returns the names of the missing ingredients for the given cocktails"""
    ingredients_in_new = []
    for cocktail in cocktails_to_add:
        ingredients_in_new.extend([i.name for i in cocktail.ingredients])
    existing_ingredients = [i.name for i in local_db.get_all_ingredients()]
    ingredient_to_add = list(set(ingredients_in_new).difference(set(existing_ingredients)))
    return ingredient_to_add


def _get_new_cocktails(new_names: List[str], default_db: DatabaseCommander, local_db: DatabaseCommander):
    """Returns the cocktails that are not already in the local db by the given names"""
    already_existing_names = [x.name for x in local_db.get_all_cocktails() if x.name in new_names]
    cocktail_difference = list(set(new_names).difference(set(already_existing_names)))
    cocktails_to_add = [x for x in default_db.get_all_cocktails() if x.name in cocktail_difference]
    return cocktails_to_add


def rename_database_to_english():
    """Renames all German columns to English ones"""
    _logger.log_event("INFO", "Renaming German column names to English ones")
    commands = [
        # Rename all bottle things
        "ALTER TABLE Belegung RENAME TO Bottles",
        "ALTER TABLE Bottles RENAME COLUMN Flasche TO Bottle",
        "ALTER TABLE Bottles DROP COLUMN Mengenlevel",
        # Rename all recipe things
        "ALTER TABLE Rezepte RENAME TO Recipes",
        "ALTER TABLE Recipes RENAME COLUMN Alkoholgehalt TO Alcohol",
        "ALTER TABLE Recipes RENAME COLUMN Menge TO Amount",
        "ALTER TABLE Recipes RENAME COLUMN Kommentar TO Comment",
        "ALTER TABLE Recipes RENAME COLUMN Anzahl TO Counter",
        "ALTER TABLE Recipes RENAME COLUMN Anzahl_Lifetime TO Counter_lifetime",
        # Rename all available things
        "ALTER TABLE Vorhanden RENAME TO Available",
        # Rename all recipe data things
        "ALTER TABLE Zusammen RENAME TO RecipeData",
        "ALTER TABLE RecipeData RENAME COLUMN Rezept_ID TO Recipe_ID",
        "ALTER TABLE RecipeData RENAME COLUMN Zutaten_ID TO Ingredient_ID",
        "ALTER TABLE RecipeData RENAME COLUMN Menge TO Amount",
        "ALTER TABLE RecipeData RENAME COLUMN Alkoholisch TO Is_alcoholic",
        # Rename all ingredient things
        "ALTER TABLE Zutaten RENAME TO Ingredients",
        "ALTER TABLE Ingredients RENAME COLUMN Alkoholgehalt TO Alcohol",
        "ALTER TABLE Ingredients RENAME COLUMN Flaschenvolumen TO Volume",
        "ALTER TABLE Ingredients RENAME COLUMN Verbrauchsmenge TO Consumption_lifetime",
        "ALTER TABLE Ingredients RENAME COLUMN Verbrauch TO Consumption",
        "ALTER TABLE Ingredients RENAME COLUMN Mengenlevel TO Fill_level",
    ]
    _try_execute_db_commands(commands)


def remove_old_recipe_columns():
    _logger.log_event("INFO", "Remove Comment from Recipes and Hand from RecipeData table")
    commands = [
        "ALTER TABLE Recipes DROP COLUMN Comment",
        "ALTER TABLE RecipeData DROP COLUMN Hand",
    ]
    _try_execute_db_commands(commands)


def _try_execute_db_commands(commands: list[str]):
    """Try to execute each command, pass if OperationalError"""
    db_handler = DatabaseHandler()
    for command in commands:
        try:
            db_handler.query_database(command)
        # this may occur if renaming already took place
        except OperationalError:
            pass


def add_more_bottles_to_db():
    """Updates the bottles to support up to 16 bottles"""
    _logger.log_event("INFO", "Adding bottle numbers 11 to 16 to DB")
    db_handler = DatabaseHandler()
    # Adding constraint if still missing
    db_handler.query_database("CREATE UNIQUE INDEX IF NOT EXISTS idx_bottle ON Bottles(Bottle)")
    for bottle_count in range(11, 17):
        db_handler.query_database("INSERT OR IGNORE INTO Bottles(Bottle) VALUES (?)", (bottle_count,))


def add_team_buffer_to_database():
    """Adds an additional table for buffering not send team data"""
    _logger.log_event("INFO", "Adding team buffer table to database")
    db_handler = DatabaseHandler()
    db_handler.query_database(
        """CREATE TABLE IF NOT EXISTS Teamdata(
            ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            Payload TEXT NOT NULL);"""
    )


def add_virgin_flag_to_db():
    """Adds the virgin flag column to the DB"""
    _logger.log_event("INFO", "Adding virgin flag column to Recipes DB")
    db_handler = DatabaseHandler()
    try:
        db_handler.query_database("ALTER TABLE Recipes ADD COLUMN Virgin INTEGER DEFAULT 0;")
        db_handler.query_database("Update Recipes SET Virgin = 0;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add virgin flag column to DB, this may because it already exists")


def add_slower_ingredient_flag_to_db():
    """Adds the slower ingredient flag column to the DB"""
    _logger.log_event("INFO", "Adding Slow flag column to Ingredients DB")
    db_handler = DatabaseHandler()
    try:
        db_handler.query_database("ALTER TABLE Ingredients ADD COLUMN Slow INTEGER DEFAULT 0;")
        db_handler.query_database("Update Ingredients SET Slow = 0;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add Slow flag column to DB, this may because it already exists")


def remove_is_alcoholic_column():
    """Removes the is_alcoholic column from the DB"""
    _logger.log_event("INFO", "Removing is_alcoholic column from DB")
    db_handler = DatabaseHandler()
    try:
        db_handler.query_database("ALTER TABLE RecipeData DROP COLUMN Is_alcoholic;")
    except OperationalError:
        _logger.log_event(
            "ERROR", "Could not remove is_alcoholic column from DB, this may because it does not exist")


def add_cost_column_to_ingredients():
    """Adds the cost column to the ingredients table"""
    _logger.log_event("INFO", "Adding cost column to Ingredients DB")
    db_handler = DatabaseHandler()
    try:
        db_handler.query_database("ALTER TABLE Ingredients ADD COLUMN Cost INTEGER DEFAULT 0;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add cost column to DB, this may because it already exists")
