import contextlib
import shutil
import sqlite3
from datetime import datetime
from sqlite3 import OperationalError

from src.filepath import BACKUP_FOLDER, DATABASE_PATH, DEFAULT_DATABASE_PATH, LOG_FOLDER
from src.logger_handler import LogFiles, LoggerHandler

_logger = LoggerHandler("update_data_module")


def execute_raw_sql(query: str, params: tuple = ()) -> None:
    """Execute raw SQL query using sqlite3."""
    if not DATABASE_PATH.exists():
        _logger.log_event("INFO", f"Copying default database from {DEFAULT_DATABASE_PATH} to {DATABASE_PATH}")
        shutil.copyfile(DEFAULT_DATABASE_PATH, DATABASE_PATH)
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()


def _try_execute_db_commands(commands: list[str]) -> None:
    """Try to execute each command, pass if OperationalError."""
    for command in commands:
        # this may occur if renaming already took place
        with contextlib.suppress(OperationalError):
            execute_raw_sql(command)


def _create_db_backup() -> None:
    """Create a backup of the current database."""
    backup_path = BACKUP_FOLDER / f"database_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
    shutil.copy(DATABASE_PATH, backup_path)
    _logger.log_event("INFO", f"Created backup of database at {backup_path}")


def fix_amount_in_recipe() -> None:
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


def remove_hand_from_recipe_data() -> None:
    """Remove the hand columns from the RecipeData table."""
    _logger.log_event("INFO", "Removing hand columns from RecipeData DB")
    try:
        execute_raw_sql("ALTER TABLE RecipeData DROP COLUMN Hand;")
    except OperationalError:
        _logger.log_event("INFO", "Could not remove hand columns from DB, this may because they do not exist")


def add_foreign_keys() -> None:
    """Add foreign keys to the database.

    Since we are working with SQLite, there is no way to add them by default.
    We will need to create a new table with the keys, copy the data and then rename the table.
    """
    # copy the database into a date-time.backup file
    _create_db_backup()
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


def add_cost_consumption_column_to_ingredients() -> None:
    """Add the cost consumption column to the Ingredients table."""
    _logger.log_event("INFO", "Adding cost consumption column to Ingredients DB")
    try:
        execute_raw_sql("ALTER TABLE Ingredients ADD COLUMN Cost_consumption_lifetime INTEGER DEFAULT 0;")
        execute_raw_sql("ALTER TABLE Ingredients ADD COLUMN Cost_consumption INTEGER DEFAULT 0;")
        # also calculate the current value (Consumption * cost / volume) since cost are per bottle volume
        execute_raw_sql(
            """UPDATE Ingredients
                SET Cost_consumption = (Consumption * Cost / Volume),
                    Cost_consumption_lifetime = (Consumption_lifetime * Cost / Volume);
            """
        )
    except OperationalError:
        _logger.log_event("INFO", "Could not add cost consumption column to DB, this may because it already exists")


def add_resource_usage_table() -> None:
    """Add the ResourceUsage table to the database."""
    _logger.log_event("INFO", "Adding ResourceUsage table to database")
    try:
        execute_raw_sql("""
            CREATE TABLE IF NOT EXISTS ResourceUsage (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp DATETIME NOT NULL DEFAULT (datetime('now')),
                CPU_Usage REAL NOT NULL,
                RAM_Usage REAL NOT NULL,
                Session INTEGER NOT NULL
            );
        """)
        execute_raw_sql("CREATE INDEX IF NOT EXISTS idx_resource_usage_session ON ResourceUsage (Session);")
    except OperationalError:
        _logger.log_event("INFO", "Could not add ResourceUsage table to DB, this may because it already exists")


def add_virgin_counters_to_recipes() -> None:
    """Add the virgin counters to the Recipes table."""
    _logger.log_event("INFO", "Adding virgin counters to Recipes DB")
    try:
        execute_raw_sql("ALTER TABLE Recipes ADD COLUMN Counter_virgin INTEGER DEFAULT 0;")
        execute_raw_sql("ALTER TABLE Recipes ADD COLUMN Counter_lifetime_virgin INTEGER DEFAULT 0;")
        execute_raw_sql("ALTER TABLE CocktailExport ADD COLUMN Counter_virgin INTEGER DEFAULT 0;")
    except OperationalError:
        _logger.log_event("INFO", "Could not add virgin counters to DB, this may because they already exist")


def clear_resource_log_file() -> None:
    """Clear the resource log file."""
    _logger.log_event("INFO", "Clearing resource log file")
    resource_log = LOG_FOLDER / f"{LogFiles.RESOURCES}.log"
    if resource_log.exists():
        with contextlib.suppress(OSError):
            resource_log.unlink()


def add_price_column_to_recipes() -> None:
    """Add the price column to the Recipes table."""
    _logger.log_event("INFO", "Adding price column to Recipes DB")
    try:
        execute_raw_sql("ALTER TABLE Recipes ADD COLUMN Price REAL DEFAULT 0.0;")
        execute_raw_sql("UPDATE Recipes SET Price = 0.0 WHERE Price IS NULL;")
    except OperationalError:
        _logger.log_event("INFO", "Could not add price column to DB, this may because it already exists")
