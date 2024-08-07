import datetime
import shutil
import sqlite3
from typing import Optional, Union

from src.filepath import DATABASE_PATH, DEFAULT_DATABASE_PATH, ROOT_PATH
from src.logger_handler import LoggerHandler
from src.models import Cocktail, Ingredient
from src.utils import time_print

_logger = LoggerHandler("database_module")


class DatabaseCommander:
    """Commander Class to execute queries and return the results as lists."""

    def __init__(self, use_default=False):
        self.handler = DatabaseHandler(use_default)

    def create_backup(self):
        """Create a backup locally in the same folder, used before migrations."""
        dtime = datetime.datetime.now()
        suffix = dtime.strftime("%Y-%m-%d-%H-%M-%S")
        full_backup_name = f"{DATABASE_PATH.stem}_backup-{suffix}.db"
        backup_path = ROOT_PATH / full_backup_name
        _logger.log_event("INFO", f"Creating backup with name: {full_backup_name}")
        _logger.log_event("INFO", f"Use this to overwrite: {DATABASE_PATH.name} in case of failure")
        shutil.copy(DATABASE_PATH, backup_path)

    def __get_recipe_ingredients_by_id(self, recipe_id: int):
        """Return ingredient data for recipe from recipe ID."""
        query = """SELECT I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level,
                I.Hand, I.Pump_speed, RD.Amount, B.Bottle, I.Cost, RD.Recipe_Order,
                I.Unit
                FROM RecipeData as RD INNER JOIN Ingredients as I
                ON RD.Ingredient_ID = I.ID
                LEFT JOIN Bottles as B ON B.ID = I.ID
                WHERE RD.Recipe_ID = ?"""
        ingredient_data = self.handler.query_database(query, (recipe_id,))
        return [
            Ingredient(
                id=i[0],
                name=i[1],
                alcohol=i[2],
                bottle_volume=i[3],
                fill_level=i[4],
                hand=bool(i[5]),
                pump_speed=i[6],
                amount=i[7],
                bottle=i[8],
                cost=i[9],
                recipe_order=i[10],
                unit=i[11],
            )
            for i in ingredient_data
        ]

    def __get_all_recipes_properties(self):
        """Get all needed data for all recipes."""
        query = "SELECT ID, Name, Alcohol, Amount, Enabled, Virgin FROM Recipes"
        return self.handler.query_database(query)

    def __build_cocktail(self, recipe_id: int, name: str, alcohol: int, amount: int, enabled: bool, virgin: bool):
        """Build one cocktail object with the given data."""
        ingredients = self.__get_recipe_ingredients_by_id(recipe_id)
        return Cocktail(recipe_id, name, alcohol, amount, bool(enabled), bool(virgin), ingredients)

    def get_cocktail(self, search: Union[str, int]) -> Optional[Cocktail]:
        """Get all needed data for the cocktail from ID or name."""
        condition = "Name" if isinstance(search, str) else "ID"
        query = f"SELECT ID, Name, Alcohol, Amount, Enabled, Virgin FROM Recipes WHERE {condition}=?"
        data = self.handler.query_database(query, (search,))
        # returns None if no data exists
        if not data:
            return None
        recipe = data[0]
        return self.__build_cocktail(*recipe)

    def get_all_cocktails(self, get_enabled=True, get_disabled=True) -> list[Cocktail]:
        """Build a list of all cocktails, option to filter by enabled status."""
        cocktails = []
        recipe_data = self.__get_all_recipes_properties()
        for recipe in recipe_data:
            enabled = bool(recipe[4])
            if (enabled and not get_enabled) or (not enabled and not get_disabled):
                continue
            cocktails.append(self.__build_cocktail(*recipe))
        return cocktails

    def get_possible_cocktails(self):
        """Return a list of currently possible cocktails with the current bottles."""
        all_cocktails = self.get_all_cocktails(get_disabled=False)
        handadds_ids = self.get_available_ids()
        return [x for x in all_cocktails if x.is_possible(handadds_ids)]

    def get_ingredient_names_at_bottles(self) -> list[str]:
        """Return ingredient name for all bottles."""
        query = """SELECT Ingredients.Name FROM Bottles
                LEFT JOIN Ingredients ON
                Ingredients.ID=Bottles.ID
                ORDER BY Bottles.Bottle"""
        result = self.handler.query_database(query)
        return [x[0] if x[0] is not None else "" for x in result]

    def get_ingredient_at_bottle(self, bottle: int) -> Ingredient:
        """Return ingredient name for all bottles."""
        query = """SELECT
                I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level, I.Hand, I.Pump_speed, B.Bottle, I.Cost, I.Unit
                FROM Bottles as B
                LEFT JOIN Ingredients as I
                ON I.ID=B.ID
                WHERE B.Bottle=?"""
        result = self.handler.query_database(query, (bottle,))
        ing = result[0]
        return Ingredient(
            id=ing[0],
            name=ing[1],
            alcohol=ing[2],
            bottle_volume=ing[3],
            fill_level=ing[4],
            hand=bool(ing[5]),
            pump_speed=ing[6],
            bottle=ing[7],
            cost=ing[8],
            unit=ing[9],
        )

    def get_bottle_fill_levels(self) -> list[int]:
        """Return percentage of fill level, limited to [0, 100]."""
        query = """SELECT Ingredients.Fill_level, Ingredients.Volume FROM Bottles
                LEFT JOIN Ingredients ON Ingredients.ID = Bottles.ID"""
        values = self.handler.query_database(query)
        levels = []
        for current_value, max_value in values:
            # restrict the value between 0 and 100
            proportion = 0
            if current_value is not None:
                proportion = round(min(max(current_value / max_value * 100, 0), 100))
            levels.append(proportion)
        return levels

    def get_ingredient(self, search: Union[str, int]) -> Optional[Ingredient]:
        """Get all needed data for the ingredient from ID or name."""
        condition = "I.Name" if isinstance(search, str) else "I.ID"
        query = f"""SELECT
                I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level, I.Hand, I.Pump_speed, B.Bottle, I.Cost, I.Unit
                FROM Ingredients as I LEFT JOIN Bottles as B on B.ID = I.ID WHERE {condition}=?"""
        data = self.handler.query_database(query, (search,))
        # returns None if no data exists
        if not data:
            return None
        ing = data[0]
        return Ingredient(
            id=ing[0],
            name=ing[1],
            alcohol=ing[2],
            bottle_volume=ing[3],
            fill_level=ing[4],
            hand=bool(ing[5]),
            pump_speed=ing[6],
            bottle=ing[7],
            cost=ing[8],
            unit=ing[9],
        )

    def get_all_ingredients(self, get_machine=True, get_hand=True) -> list[Ingredient]:
        """Build a list of all ingredients, option to filter by add status."""
        ingredients = []
        query = """SELECT
                I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level, I.Hand, I.Pump_speed, B.Bottle, I.Cost, I.Unit
                FROM Ingredients as I LEFT JOIN Bottles as B on B.ID = I.ID"""
        ingredient_data = self.handler.query_database(query)
        for ing in ingredient_data:
            hand = bool(ing[5])
            if (not hand and get_machine) or (hand and get_hand):
                ingredients.append(
                    Ingredient(
                        id=ing[0],
                        name=ing[1],
                        alcohol=ing[2],
                        bottle_volume=ing[3],
                        fill_level=ing[4],
                        hand=hand,
                        pump_speed=ing[6],
                        bottle=ing[7],
                        cost=ing[8],
                        unit=ing[9],
                    )
                )
        return ingredients

    def get_bottle_usage(self, ingredient_id: int):
        """Return if the ingredient id is currently used at a bottle."""
        query = "SELECT COUNT(*) FROM Bottles WHERE ID = ?"
        return bool(self.handler.query_database(query, (ingredient_id,))[0][0])

    def get_recipe_usage_list(self, ingredient_id: int) -> list[str]:
        """Get all the recipe names the ingredient is used in."""
        query = """SELECT Recipes.Name FROM RecipeData
                INNER JOIN Recipes ON Recipes.ID = RecipeData.Recipe_ID
                WHERE RecipeData.Ingredient_ID=?"""
        recipe_list = self.handler.query_database(query, (ingredient_id,))
        return [recipe[0] for recipe in recipe_list]

    def __get_multiple_ingredient_ids_from_names(self, name_list: list[str]) -> list[int]:
        """Get all the ids for the selected names."""
        question_marks = ",".join(["?"] * len(name_list))
        query = f"SELECT ID FROM Ingredients WHERE Name in ({question_marks})"
        result = self.handler.query_database(query, name_list)
        return [x[0] for x in result]

    def get_consumption_data_lists_recipes(self):
        """Return the recipe consumption data ready to export."""
        query = "SELECT Name, Counter, Counter_lifetime FROM Recipes"
        data = self.handler.query_database(query)
        return self.__convert_consumption_data(data)

    def get_consumption_data_lists_ingredients(self):
        """Return the ingredient consumption data ready to export."""
        query = """SELECT Name, Consumption, Consumption_lifetime,
                Consumption*Cost AS Cost, Consumption_lifetime*Cost AS Cost_lifetime
                FROM Ingredients"""
        data = self.handler.query_database(query)
        return self.__convert_consumption_data(data)

    def get_cost_data_lists_ingredients(self):
        """Return the ingredient cost data ready to export."""
        query = """SELECT Name, Consumption*Cost/1000 AS Cost, Consumption_lifetime*Cost/1000 AS Cost_lifetime
                FROM Ingredients"""
        data = self.handler.query_database(query)
        return self.__convert_consumption_data(data)

    def __convert_consumption_data(self, data: list[list]):
        """Convert the data from the db cursor into needed csv format."""
        headers = [row[0] for row in data]
        resettable = [row[1] for row in data]
        lifetime = [row[2] for row in data]
        return [["date", *headers], [datetime.date.today(), *resettable], ["lifetime", *lifetime]]

    def get_available_ingredient_names(self) -> list[str]:
        """Get the names for the available ingredients."""
        query = """SELECT Ingredients.Name FROM Ingredients
                INNER JOIN Available ON Available.ID = Ingredients.ID"""
        data = self.handler.query_database(query)
        return [x[0] for x in data]

    def get_available_ids(self) -> list[int]:
        """Return a list of the IDs of all available defined ingredients."""
        query = "SELECT ID FROM Available"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_bottle_data_bottle_window(self):
        """Get all needed data for bottles, ordered by bottle number.

        Returns [name, level, id, bottle_volume] for each slot.
        """
        query = """SELECT Ingredients.Name, Ingredients.Fill_level, Ingredients.ID, Ingredients.Volume
                FROM Bottles LEFT JOIN Ingredients ON Ingredients.ID = Bottles.ID ORDER BY Bottles.Bottle"""
        return self.handler.query_database(query)

    def get_ingredient_bottle_and_level_by_name(self, ingredient_name):
        """Return (Bottle_number, level) for the given ingredient."""
        query = """SELECT Bottles.Bottle, Ingredients.Fill_level
                FROM Bottles INNER JOIN Ingredients ON Ingredients.ID = Bottles.ID
                WHERE Ingredients.Name = ?"""
        data = self.handler.query_database(query, (ingredient_name,))
        if data:
            return data[0][0], data[0][1]
        return 0, 0

    # set (update) commands
    def set_bottle_order(self, ingredient_names: list[str]):
        """Set bottles to the given list of bottles, need all bottles."""
        for i, ingredient in enumerate(ingredient_names):
            bottle = i + 1
            query = """UPDATE OR IGNORE Bottles
                    SET ID = (SELECT ID FROM Ingredients WHERE Name = ?)
                    WHERE Bottle = ?"""
            search_tuple = (ingredient, bottle)
            self.handler.query_database(query, search_tuple)

    def set_bottle_volumelevel_to_max(self, bottle_number_list: list[int]):
        """Set the each i-th bottle to max level if arg is true."""
        query = """UPDATE OR IGNORE Ingredients
                Set Fill_level = Volume
                WHERE ID = (SELECT ID FROM Bottles WHERE Bottle = ?)"""
        for bottle in bottle_number_list:
            self.handler.query_database(query, (bottle,))

    def set_ingredient_data(
        self,
        ingredient_name: str,
        alcohol_level: int,
        volume: int,
        new_level: int,
        only_hand: bool,
        pump_speed: int,
        ingredient_id: int,
        cost: int,
        unit: str,
    ):
        """Update the given ingredient id to new properties."""
        query = """UPDATE OR IGNORE Ingredients
                SET Name = ?, Alcohol = ?,
                Volume = ?,
                Fill_level = ?,
                Hand = ?,
                Pump_speed = ?,
                Cost = ?,
                Unit = ?
                WHERE ID = ?"""
        search_tuple = (
            ingredient_name,
            alcohol_level,
            volume,
            new_level,
            int(only_hand),
            pump_speed,
            cost,
            unit,
            ingredient_id,
        )
        self.handler.query_database(query, search_tuple)

    def increment_recipe_counter(self, recipe_name: str):
        """Increase the recipe counter by one of given recipe name."""
        query = """UPDATE OR IGNORE Recipes
                SET Counter_lifetime = Counter_lifetime + 1,
                Counter = Counter + 1
                WHERE Name = ?"""
        self.handler.query_database(query, (recipe_name,))

    def increment_ingredient_consumption(self, ingredient_name: str, ingredient_consumption: int):
        """Increase the consumption of given ingredient name by a given amount."""
        query = """UPDATE OR IGNORE Ingredients
                SET Consumption_lifetime = Consumption_lifetime + ?,
                Consumption = Consumption + ?,
                Fill_level = Fill_level - ?
                WHERE Name = ?"""
        search_tuple = (ingredient_consumption, ingredient_consumption, ingredient_consumption, ingredient_name)
        self.handler.query_database(query, search_tuple)

    def set_multiple_ingredient_consumption(
        self, ingredient_name_list: list[str], ingredient_consumption_list: list[int]
    ):
        """Increase multiple ingredients by the according given consumption."""
        for ingredient_name, ingredient_consumption in zip(ingredient_name_list, ingredient_consumption_list):
            self.increment_ingredient_consumption(ingredient_name, ingredient_consumption)

    def set_all_recipes_enabled(self):
        """Enable all recipes."""
        query = "UPDATE OR IGNORE Recipes SET Enabled = 1"
        self.handler.query_database(query)

    def set_recipe(self, recipe_id: int, name: str, alcohol_level: int, volume: int, enabled: int, virgin: int):
        """Update the given recipe id to new properties."""
        query = """UPDATE OR IGNORE Recipes
                SET Name = ?, Alcohol = ?, Amount = ?, Enabled = ?, Virgin = ?
                WHERE ID = ?"""
        search_tuple = (name, alcohol_level, volume, enabled, virgin, recipe_id)
        self.handler.query_database(query, search_tuple)

    def set_ingredient_level_to_value(self, ingredient_id: int, value: int):
        """Set the given ingredient id to a defined level."""
        query = "UPDATE OR IGNORE Ingredients SET Fill_level = ? WHERE ID = ?"
        self.handler.query_database(query, (value, ingredient_id))

    # insert commands
    def insert_new_ingredient(
        self,
        ingredient_name: str,
        alcohol_level: int,
        volume: int,
        only_hand: bool,
        pump_speed: int,
        cost: int,
        unit: str,
    ):
        """Insert a new ingredient into the database."""
        query = """INSERT OR IGNORE INTO
                Ingredients(
                    Name, Alcohol, Volume, Consumption_lifetime, Consumption, Fill_level, Hand, Pump_speed, Cost, Unit
                )
                VALUES (?,?,?,0,0,0,?,?,?,?)"""
        search_tuple = (ingredient_name, alcohol_level, volume, int(only_hand), pump_speed, cost, unit)
        self.handler.query_database(query, search_tuple)

    def insert_new_recipe(self, name: str, alcohol_level: int, volume: int, enabled: int, virgin: int):
        """Insert a new recipe into the database."""
        query = """INSERT OR IGNORE INTO
                Recipes(Name, Alcohol, Amount, Counter_lifetime, Counter, Enabled, Virgin)
                VALUES (?,?,?,0,0,?,?)"""
        search_tuple = (name, alcohol_level, volume, enabled, virgin)
        self.handler.query_database(query, search_tuple)

    def insert_recipe_data(self, recipe_id: int, ingredient_id: int, ingredient_volume: int, order_number: int):
        """Insert given data into the recipe_data table."""
        query = "INSERT OR IGNORE INTO RecipeData(Recipe_ID, Ingredient_ID, Amount, Recipe_Order) VALUES (?, ?, ?, ?)"
        search_tuple = (recipe_id, ingredient_id, ingredient_volume, order_number)
        self.handler.query_database(query, search_tuple)

    def insert_multiple_existing_handadd_ingredients_by_name(self, ingredient_names: list[str]):
        """Insert the IDS of the given ingredient list into the available table."""
        ingredient_id = self.__get_multiple_ingredient_ids_from_names(ingredient_names)
        question_marks = ",".join(["(?)"] * len(ingredient_id))
        query = f"INSERT INTO Available(ID) VALUES {question_marks}"
        self.handler.query_database(query, ingredient_id)

    # delete
    def delete_ingredient(self, ingredient_id: int):
        """Delete an ingredient by id."""
        query = "DELETE FROM Ingredients WHERE ID = ?"
        self.handler.query_database(query, (ingredient_id,))

    def delete_consumption_recipes(self):
        """Set the resettable consumption of all recipes to zero."""
        query = "UPDATE OR IGNORE Recipes SET Counter = 0"
        self.handler.query_database(query)

    def delete_consumption_ingredients(self):
        """Set the resettable consumption of all ingredients to zero."""
        query = "UPDATE OR IGNORE Ingredients SET Consumption = 0"
        self.handler.query_database(query)

    def delete_recipe(self, recipe_name: str):
        """Delete the given recipe by name and all according ingredient_data."""
        # if using FK with cascade delete, this will prob no longer necessary
        query1 = "DELETE FROM RecipeData WHERE Recipe_ID = (SELECT ID FROM Recipes WHERE Name = ?)"
        query2 = "DELETE FROM Recipes WHERE Name = ?"
        self.handler.query_database(query1, (recipe_name,))
        self.handler.query_database(query2, (recipe_name,))

    def delete_recipe_ingredient_data(self, recipe_id: int):
        """Delete ingredient_data by given ID."""
        query = "DELETE FROM RecipeData WHERE Recipe_ID = ?"
        self.handler.query_database(query, (recipe_id,))

    def delete_existing_handadd_ingredient(self):
        """Delete all ingredient in the available table."""
        self.handler.query_database("DELETE FROM Available")

    def delete_database_data(self):
        """Remove all the data from the db for a local reset."""
        commands = [
            "DELETE FROM Available",
            "UPDATE Bottles set ID = Null",
            "DELETE FROM RecipeData",
            "DELETE FROM Recipes",
            "DELETE FROM Ingredients",
        ]
        for command in commands:
            self.handler.query_database(command)

    def save_failed_teamdata(self, payload):
        """Save the failed payload into the db to buffer."""
        self.handler.query_database("INSERT INTO Teamdata(Payload) VALUES(?)", (payload,))

    def get_failed_teamdata(self):
        """Return one failed teamdata payload."""
        data = self.handler.query_database("SELECT * FROM Teamdata ORDER BY ID ASC LIMIT 1")
        if data:
            return data[0]
        return []

    def delete_failed_teamdata(self, data_id):
        """Delete the given teamdata by id."""
        self.handler.query_database("DELETE FROM Teamdata WHERE ID=?", (data_id,))


class DatabaseHandler:
    """Handler Class for Connecting and querying Databases."""

    database_path = DATABASE_PATH
    database_path_default = DEFAULT_DATABASE_PATH

    def __init__(self, use_default=False):
        self.database_path = DatabaseHandler.database_path
        if not self.database_path_default.exists():
            time_print("Creating Database")
            self.create_tables()
        if not self.database_path.exists():
            time_print("Copying default database for maker usage")
            self.copy_default_database()
        if use_default:
            self.connect_database(str(self.database_path_default.absolute()))
        else:
            self.connect_database()

    def connect_database(self, path: Optional[str] = None):
        """Connect to the given path or local database, creates cursor."""
        if path:
            self.database = sqlite3.connect(path)
        else:
            self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()

    def query_database(self, sql: str, search_tuple=()):
        """Execute the given query, if select command, return the data."""
        self.cursor.execute(sql, search_tuple)

        if sql.lower().strip()[0:6] == "select":
            result = self.cursor.fetchall()
        else:
            self.database.commit()
            result = []

        return result

    def copy_default_database(self):
        """Create a local copy of the database."""
        shutil.copy(self.database_path_default, self.database_path)

    def create_tables(self):
        """Create all needed tables and constraints."""
        self.connect_database(str(self.database_path_default))
        # Creates each Table
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Recipes(
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Name TEXT NOT NULL,
                Alcohol INTEGER NOT NULL,
                Amount INTEGER NOT NULL,
                Counter_lifetime INTEGER,
                Counter INTEGER,
                Enabled INTEGER);"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Ingredients(
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Name TEXT NOT NULL,
                Alcohol INTEGER NOT NULL,
                Volume INTEGER NOT NULL,
                Consumption_lifetime INTEGER,
                Consumption INTEGER,
                Fill_level INTEGER,
                Hand INTEGER,
                Cost INTEGER);"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS RecipeData(
                Recipe_ID INTEGER NOT NULL,
                Ingredient_ID INTEGER NOT NULL,
                Amount INTEGER NOT NULL,
                CONSTRAINT fk_data_ingredient
                    FOREIGN KEY (Ingredient_ID)
                    REFERENCES Ingredients (ID)
                    ON DELETE RESTRICT,
                CONSTRAINT fk_data_recipe
                    FOREIGN KEY (Recipe_ID)
                    REFERENCES Recipes (ID)
                    ON DELETE CASCADE
                );"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Bottles(
                Bottle INTEGER NOT NULL,
                ID INTEGER,
                CONSTRAINT fk_bottle_ingredient
                    FOREIGN KEY (ID)
                    REFERENCES Ingredients (ID)
                    ON DELETE RESTRICT
                );"""
        )
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Available(ID INTEGER NOT NULL);")

        # Creating the Unique Indexes
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ingredient_name ON Ingredients(Name)")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_recipe_name ON Recipes(Name)")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_bottle ON Bottles(Bottle)")

        # Creating the Space Naming of the Bottles
        for bottle_count in range(1, 13):
            self.cursor.execute("INSERT INTO Bottles(Bottle) VALUES (?)", (bottle_count,))
        self.database.commit()
        self.database.close()


DB_COMMANDER = DatabaseCommander()
