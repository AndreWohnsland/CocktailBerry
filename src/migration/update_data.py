import contextlib
import shutil
import sqlite3
from datetime import datetime
from sqlite3 import OperationalError

from src.filepath import BACKUP_FOLDER, DATABASE_PATH, DEFAULT_DATABASE_PATH
from src.logger_handler import LoggerHandler

_logger = LoggerHandler("update_data_module")


def execute_raw_sql(query: str, params: tuple = ()):
    """Execute raw SQL query using sqlite3."""
    if not DATABASE_PATH.exists():
        _logger.log_event("INFO", f"Copying default database from {DEFAULT_DATABASE_PATH} to {DATABASE_PATH}")
        shutil.copyfile(DEFAULT_DATABASE_PATH, DATABASE_PATH)
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()


def rename_database_to_english():
    """Rename all German columns to English ones."""
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
    """Try to execute each command, pass if OperationalError."""
    for command in commands:
        # this may occur if renaming already took place
        with contextlib.suppress(OperationalError):
            execute_raw_sql(command)


def add_more_bottles_to_db():
    """Update the bottles to support up to 16 bottles."""
    _logger.log_event("INFO", "Adding bottle numbers 11 to 16 to DB")
    # Adding constraint if still missing
    execute_raw_sql("CREATE UNIQUE INDEX IF NOT EXISTS idx_bottle ON Bottles(Bottle)")
    for bottle_count in range(11, 17):
        execute_raw_sql("INSERT OR IGNORE INTO Bottles(Bottle) VALUES (?)", (bottle_count,))


def add_team_buffer_to_database():
    """Add an additional table for buffering not send team data."""
    _logger.log_event("INFO", "Adding team buffer table to database")
    execute_raw_sql(
        """CREATE TABLE IF NOT EXISTS Teamdata(
            ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            Payload TEXT NOT NULL);"""
    )


def add_virgin_flag_to_db():
    """Add the virgin flag column to the DB."""
    _logger.log_event("INFO", "Adding virgin flag column to Recipes DB")
    try:
        execute_raw_sql("ALTER TABLE Recipes ADD COLUMN Virgin INTEGER DEFAULT 0;")
        execute_raw_sql("Update Recipes SET Virgin = 0;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add virgin flag column to DB, this may because it already exists")


def add_slower_ingredient_flag_to_db():
    """Add the slower ingredient flag column to the DB."""
    _logger.log_event("INFO", "Adding Slow flag column to Ingredients DB")
    try:
        execute_raw_sql("ALTER TABLE Ingredients ADD COLUMN Slow INTEGER DEFAULT 0;")
        execute_raw_sql("Update Ingredients SET Slow = 0;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add Slow flag column to DB, this may because it already exists")


def remove_is_alcoholic_column():
    """Remove the is_alcoholic column from the DB."""
    _logger.log_event("INFO", "Removing is_alcoholic column from DB")
    try:
        execute_raw_sql("ALTER TABLE RecipeData DROP COLUMN Is_alcoholic;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not remove is_alcoholic column from DB, this may because it does not exist")


def add_cost_column_to_ingredients():
    """Add the cost column to the ingredients table."""
    _logger.log_event("INFO", "Adding cost column to Ingredients DB")
    try:
        execute_raw_sql("ALTER TABLE Ingredients ADD COLUMN Cost INTEGER DEFAULT 0;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add cost column to DB, this may because it already exists")


def add_order_column_to_ingredient_data():
    """Add the order column to the RecipeData table."""
    _logger.log_event("INFO", "Adding Recipe_Order column to RecipeData DB")
    try:
        execute_raw_sql("ALTER TABLE RecipeData ADD COLUMN Recipe_Order INTEGER DEFAULT 1;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add order column to DB, this may because it already exists")


def add_unit_column_to_ingredients():
    """Add the unit column to the Ingredients table."""
    _logger.log_event("INFO", "Adding unit column to Ingredients DB")
    try:
        execute_raw_sql("ALTER TABLE Ingredients ADD COLUMN Unit TEXT DEFAULT 'ml';")
    except OperationalError:
        _logger.log_event("ERROR", "Could not add unit column to DB, this may because it already exists")


def change_slower_flag_to_pump_speed(slow_factor: float):
    """Add the pump speed column to the Ingredients table.

    Removes the slow flag column from the Ingredients table.
    """
    pump_speed = int(100 * slow_factor)
    _logger.log_event(
        "INFO", f"Converting Slow flag to Pump Speed column in Ingredients DB, using slow factor {slow_factor}"
    )
    try:
        execute_raw_sql("ALTER TABLE Ingredients ADD COLUMN Pump_speed INTEGER DEFAULT 100;")
        execute_raw_sql("UPDATE Ingredients SET Pump_speed = ? WHERE Slow = 1;", (pump_speed,))
        execute_raw_sql("ALTER TABLE Ingredients DROP COLUMN Slow;")
    except OperationalError:
        _logger.log_event(
            "ERROR", "Could not convert slow flag to pump speed column in DB, this may because it was already done"
        )


def fix_amount_in_recipe():
    """Recalculate the amount in the Recipe table."""
    _logger.log_event("INFO", "Adding team buffer table to database")
    execute_raw_sql(
        """UPDATE Recipes
            SET Amount = (
                SELECT SUM(Amount)
                FROM RecipeData
                WHERE RecipeData.Recipe_ID = Recipes.ID
                GROUP BY RecipeData.Recipe_ID
            );"""
    )


def remove_hand_from_recipe_data():
    """Remove the hand columns from the RecipeData table."""
    _logger.log_event("INFO", "Removing hand columns from RecipeData DB")
    try:
        execute_raw_sql("ALTER TABLE RecipeData DROP COLUMN Hand;")
    except OperationalError:
        _logger.log_event("ERROR", "Could not remove hand columns from DB, this may because they do not exist")


def add_foreign_keys():
    """Add foreign keys to the database.

    Since we are working with SQLite, there is no way to add them by default.
    We will need to create a new table with the keys, copy the data and then rename the table.
    """
    # copy the database into a date-time.backup file

    backup_path = BACKUP_FOLDER / f"database_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
    shutil.copy(DATABASE_PATH, backup_path)
    _logger.log_event("INFO", f"Created backup of database at {backup_path}")
    _logger.log_event("INFO", "Adding foreign keys to the database")
    execute_raw_sql("PRAGMA foreign_keys=off;")
    execute_raw_sql("""
        CREATE TABLE RecipeData_new (
            Recipe_ID INTEGER NOT NULL,
            Ingredient_ID INTEGER NOT NULL,
            Amount INTEGER NOT NULL,
            Recipe_Order INTEGER DEFAULT 1,
            PRIMARY KEY (Recipe_ID, Ingredient_ID),
            FOREIGN KEY (Recipe_ID) REFERENCES Recipes(ID) ON DELETE CASCADE,
            FOREIGN KEY (Ingredient_ID) REFERENCES Ingredients(ID) ON DELETE RESTRICT
        );
    """)
    execute_raw_sql("""
        INSERT INTO RecipeData_new (Recipe_ID, Ingredient_ID, Amount, Recipe_Order)
        SELECT Recipe_ID, Ingredient_ID, Amount, Recipe_Order FROM RecipeData;
    """)
    execute_raw_sql("DROP TABLE RecipeData;")
    execute_raw_sql("ALTER TABLE RecipeData_new RENAME TO RecipeData;")
    execute_raw_sql("CREATE INDEX idx_recipe_data_recipe_id ON RecipeData (Recipe_ID);")
    execute_raw_sql("CREATE INDEX idx_recipe_data_ingredient_id ON RecipeData (Ingredient_ID);")
    execute_raw_sql("""
        CREATE TABLE Bottles_new (
            Bottle INTEGER PRIMARY KEY NOT NULL,
            ID INTEGER,
            FOREIGN KEY (ID) REFERENCES Ingredients(ID) ON DELETE RESTRICT
        );
    """)
    execute_raw_sql("""
        INSERT INTO Bottles_new (Bottle, ID)
        SELECT Bottle, ID FROM Bottles;
    """)
    execute_raw_sql("DROP TABLE Bottles;")
    execute_raw_sql("ALTER TABLE Bottles_new RENAME TO Bottles;")
    execute_raw_sql("CREATE INDEX idx_bottles_id ON Bottles (ID);")
    execute_raw_sql("""
        CREATE TABLE Available_new (
            ID INTEGER PRIMARY KEY NOT NULL,
            FOREIGN KEY (ID) REFERENCES Ingredients(ID)
        );
    """)
    execute_raw_sql("""
        INSERT INTO Available_new (ID)
        SELECT ID FROM Available;
    """)
    execute_raw_sql("DROP TABLE Available;")
    execute_raw_sql("ALTER TABLE Available_new RENAME TO Available;")
    execute_raw_sql("CREATE INDEX idx_available_id ON Available (ID);")
    execute_raw_sql("PRAGMA foreign_keys=on;")
