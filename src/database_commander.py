import datetime
import shutil
from pathlib import Path
import sqlite3
from typing import List, Optional, Union

from src.models import Cocktail, Ingredient

DATABASE_NAME = "Cocktail_database"
DIRPATH = Path(__file__).parent.absolute()


class DatabaseCommander:
    """Commander Class to execute queries and return the results as lists """

    def __init__(self):
        self.handler = DatabaseHandler()

    def __get_recipe_ingredients_by_id(self, recipe_id: int):
        """Return ingredient data for recipe from recipe ID"""
        query = """SELECT I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level,
                I.Hand, RD.Amount, RD.Hand, B.Bottle
                FROM RecipeData as RD INNER JOIN Ingredients as I 
                ON RD.Ingredient_ID = I.ID
                LEFT JOIN Bottles as B ON B.ID = I.ID
                WHERE RD.Recipe_ID = ?"""
        return self.handler.query_database(query, (recipe_id,))

    def __get_all_recipes_properties(self):
        """Get all neeeded data for all recipes"""
        query = "SELECT ID, Name, Alcohol, Amount, Comment, Enabled, Virgin FROM Recipes"
        return self.handler.query_database(query)

    def __build_cocktail(self, recipe_id: int, name: str, alcohol: int, amount: int, comment: str, enabled: bool, virgin: bool):
        """Build one cocktail object with the given data"""
        ingredient_data = self.__get_recipe_ingredients_by_id(recipe_id)
        return Cocktail(
            recipe_id, name, alcohol, amount, comment, bool(enabled), bool(virgin),
            [Ingredient(
                i[0], i[1], i[2], i[3], i[4], bool(i[5]), i[6], bool(i[7]), i[8]
            ) for i in ingredient_data]
        )

    def get_cocktail(self, search: Union[str, int]) -> Union[Cocktail, None]:
        """Get all neeeded data for the cocktail from ID or name"""
        if isinstance(search, str):
            condition = "Name"
        else:
            condition = "ID"
        query = f"SELECT ID, Name, Alcohol, Amount, Comment, Enabled, Virgin FROM Recipes WHERE {condition}=?"
        data = self.handler.query_database(query, (search,))
        # returns None if no data exists
        if not data:
            return None
        recipe = data[0]
        return self.__build_cocktail(*recipe)

    def get_all_cocktails(self, get_enabled=True, get_disabled=True) -> List[Cocktail]:
        """Bilds a list of all cocktails, option to filter by enabled status"""
        cocktails = []
        recipe_data = self.__get_all_recipes_properties()
        for recipe in recipe_data:
            enabled = bool(recipe[5])
            if (enabled and not get_enabled) or (not enabled and not get_disabled):
                continue
            cocktails.append(self.__build_cocktail(*recipe))
        return cocktails

    def get_ingredients_at_bottles(self) -> List[str]:
        """Return ingredient name for all bottles"""
        query = """SELECT Ingredients.Name FROM Bottles
                    LEFT JOIN Ingredients ON
                    Ingredients.ID=Bottles.ID
                    ORDER BY Bottles.Bottle"""
        result = self.handler.query_database(query)
        return [x[0] if x[0] is not None else "" for x in result]

    def get_bottle_fill_levels(self) -> List[int]:
        """Returns percentage of fill level, limited to [0, 100]"""
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

    def get_ingredient(self, search: Union[str, int]) -> Union[Ingredient, None]:
        """Get all neeeded data for the ingredient from ID or name"""
        if isinstance(search, str):
            condition = "I.Name"
        else:
            condition = "I.ID"
        query = "SELECT I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level, I.Hand, B.Bottle " + \
            f"FROM Ingredients as I LEFT JOIN Bottles as B on B.ID = I.ID WHERE {condition}=?"
        data = self.handler.query_database(query, (search,))
        # returns None if no data exists
        if not data:
            return None
        ing = data[0]
        return Ingredient(ing[0], ing[1], ing[2], ing[3], ing[4], bool(ing[5]), bottle=ing[6])

    def get_all_ingredients(self, get_machine=True, get_hand=True) -> List[Ingredient]:
        """Bilds a list of all ingredinets, option to filter by add status"""
        ingredients = []
        query = """SELECT I.ID, I.Name, I.Alcohol, I.Volume, I.Fill_level, I.Hand, B.Bottle
                    FROM Ingredients as I LEFT JOIN Bottles as B on B.ID = I.ID"""
        ingredient_data = self.handler.query_database(query)
        for ing in ingredient_data:
            hand = bool(ing[5])
            if (not hand and get_machine) or (hand and get_hand):
                ingredients.append(Ingredient(ing[0], ing[1], ing[2], ing[3], ing[4], hand, bottle=ing[6]))
        return ingredients

    def get_bottle_usage(self, ingredient_id: int):
        """Returns if the ingredient id is currently used at a bottle"""
        query = "SELECT COUNT(*) FROM Bottles WHERE ID = ?"
        if self.handler.query_database(query, (ingredient_id,))[0][0]:
            return True
        return False

    def get_recipe_usage_list(self, ingredient_id: int) -> List[str]:
        """Get all the recipe names the ingredient is used in"""
        query = """SELECT Recipes.Name FROM RecipeData
                INNER JOIN Recipes ON Recipes.ID = RecipeData.Recipe_ID 
                WHERE RecipeData.Ingredient_ID=?"""
        recipe_list = self.handler.query_database(query, (ingredient_id,))
        return [recipe[0] for recipe in recipe_list]

    def __get_multiple_ingredient_ids_from_names(self, name_list: List[str]) -> List[int]:
        """Get all the ids for the selected names"""
        questionmarks = ",".join(["?"] * len(name_list))
        query = f"SELECT ID FROM Ingredients WHERE Name in ({questionmarks})"
        result = self.handler.query_database(query, name_list)
        return [x[0] for x in result]

    def get_consumption_data_lists_recipes(self):
        """Return the recipe consumption data ready to export"""
        query = "SELECT Name, Counter, Counter_lifetime FROM Recipes"
        data = self.handler.query_database(query)
        return self.__convert_consumption_data(data)

    def get_consumption_data_lists_ingredients(self):
        """Return the ingredient consumption data ready to export"""
        query = "SELECT Name, Consumption, Consumption_lifetime FROM Ingredients"
        data = self.handler.query_database(query)
        return self.__convert_consumption_data(data)

    def __convert_consumption_data(self, data: List[List]):
        """Convert the data from the db cursor into needed csv format"""
        headers = [row[0] for row in data]
        resetable = [row[1] for row in data]
        lifetime = [row[2] for row in data]
        return [["date", *headers], [datetime.date.today(), *resetable], ["lifetime", *lifetime]]

    def get_available_ingredient_names(self) -> List[str]:
        """Get the names for the available ingredients"""
        query = """SELECT Ingredients.Name FROM Ingredients
                INNER JOIN Available ON Available.ID = Ingredients.ID"""
        data = self.handler.query_database(query)
        return [x[0] for x in data]

    def get_available_ids(self) -> List[int]:
        """Returns a list of the IDs of all available defined ingredients"""
        query = "SELECT ID FROM Available"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_bottle_data_bottle_window(self):
        """Gets all needed data for bottles, ordered by bottle number
        Returs [name, level, id, bottle_volume] for each slot"""
        query = """SELECT Ingredients.Name, Ingredients.Fill_level, Ingredients.ID, Ingredients.Volume
                FROM Bottles LEFT JOIN Ingredients ON Ingredients.ID = Bottles.ID ORDER BY Bottles.Bottle"""
        return self.handler.query_database(query)

    def get_ingredient_bottle_and_level_by_name(self, ingredient_name):
        """Returns (Bottle_number, level) for the given ingredient"""
        query = """SELECT Bottles.Bottle, Ingredients.Fill_level
                FROM Bottles INNER JOIN Ingredients ON Ingredients.ID = Bottles.ID
                WHERE Ingredients.Name = ?"""
        data = self.handler.query_database(query, (ingredient_name,))
        if data:
            return data[0][0], data[0][1]
        return 0, 0

    # set (update) commands
    def set_bottleorder(self, ingredient_names: List[str]):
        """Set bottles to the given list of bottles, need all bottles"""
        for i, ingredient in enumerate(ingredient_names):
            bottle = i + 1
            query = """UPDATE OR IGNORE Bottles
                    SET ID = (SELECT ID FROM Ingredients WHERE Name = ?)
                    WHERE Bottle = ?"""
            searchtuple = (ingredient, bottle)
            self.handler.query_database(query, searchtuple)

    def set_bottle_volumelevel_to_max(self, boolean_list: List[bool]):
        """Sets the each i-th bottle to max level if arg is true"""
        query = """UPDATE OR IGNORE Ingredients
                Set Fill_level = Volume
                WHERE ID = (SELECT ID FROM Bottles WHERE Bottle = ?)"""
        for bottle, set_to_max in enumerate(boolean_list, start=1):
            if set_to_max:
                self.handler.query_database(query, (bottle,))

    def set_ingredient_data(self, ingredient_name: str, alcohollevel: int, volume: int, new_level: int, onlyhand: bool, ingredient_id: int):
        """Updates the given ingredient id to new properties"""
        query = """UPDATE OR IGNORE Ingredients
                SET Name = ?, Alcohol = ?,
                Volume = ?,
                Fill_level = ?,
                Hand = ?
                WHERE ID = ?"""
        searchtuple = (ingredient_name, alcohollevel, volume, new_level, int(onlyhand), ingredient_id)
        self.handler.query_database(query, searchtuple)

    def increment_recipe_counter(self, recipe_name: str):
        """Increase the recipe counter by one of given recipe name"""
        query = """UPDATE OR IGNORE Recipes
                SET Counter_lifetime = Counter_lifetime + 1, 
                Counter = Counter + 1 
                WHERE Name = ?"""
        self.handler.query_database(query, (recipe_name,))

    def increment_ingredient_consumption(self, ingredient_name: str, ingredient_consumption: int):
        """Increase the consumption of given ingredient name by a given amount"""
        query = """UPDATE OR IGNORE Ingredients
                SET Consumption_lifetime = Consumption_lifetime + ?, 
                Consumption = Consumption + ?, 
                Fill_level = Fill_level - ? 
                WHERE Name = ?"""
        searchtuple = (ingredient_consumption, ingredient_consumption, ingredient_consumption, ingredient_name)
        self.handler.query_database(query, searchtuple)

    def set_multiple_ingredient_consumption(self, ingredient_name_list: List[str], ingredient_consumption_list: List[int]):
        """Increase multiple ingredients by the according given comsuption"""
        for ingredient_name, ingredient_consumption in zip(ingredient_name_list, ingredient_consumption_list):
            self.increment_ingredient_consumption(ingredient_name, ingredient_consumption)

    def set_all_recipes_enabled(self):
        """Enables all recipes"""
        query = "UPDATE OR IGNORE Recipes SET Enabled = 1"
        self.handler.query_database(query)

    def set_recipe(self, recipe_id: int, name: str, alcohollevel: int, volume: int, comment: str, enabled: int, virgin: int):
        """Updates the given recipe id to new properties"""
        query = """UPDATE OR IGNORE Recipes
                SET Name = ?, Alcohol = ?, Amount = ?, Comment = ?, Enabled = ?, Virgin = ?
                WHERE ID = ?"""
        searchtuple = (name, alcohollevel, volume, comment, enabled, virgin, recipe_id)
        self.handler.query_database(query, searchtuple)

    def set_ingredient_level_to_value(self, ingredient_id: int, value: int):
        """Sets the given ingredient id to a defined level"""
        query = "UPDATE OR IGNORE Ingredients SET Fill_level = ? WHERE ID = ?"
        self.handler.query_database(query, (value, ingredient_id))

    # insert commands
    def insert_new_ingredient(self, ingredient_name: str, alcohollevel: int, volume: int, onlyhand: bool):
        """Insert a new ingredient into the database"""
        query = """INSERT OR IGNORE INTO
                Ingredients(Name,Alcohol,Volume,Consumption_lifetime,Consumption,Fill_level,Hand) 
                VALUES (?,?,?,0,0,0,?)"""
        searchtuple = (ingredient_name, alcohollevel, volume, int(onlyhand))
        self.handler.query_database(query, searchtuple)

    def insert_new_recipe(self, name: str, alcohollevel: int, volume: int, comment: str, enabled: int, virgin: int):
        """Insert a new recipe into the database"""
        query = """INSERT OR IGNORE INTO
                Recipes(Name, Alcohol, Amount, Comment, Counter_lifetime, Counter, Enabled, Virgin) 
                VALUES (?,?,?,?,0,0,?,?)"""
        searchtuple = (name, alcohollevel, volume, comment, enabled, virgin)
        self.handler.query_database(query, searchtuple)

    def insert_recipe_data(self, recipe_id: int, ingredient_id: int, ingredient_volume: int, hand_add: bool):
        """Insert given data into the recipe_data table"""
        query = "INSERT OR IGNORE INTO RecipeData(Recipe_ID, Ingredient_ID, Amount, Hand) VALUES (?, ?, ?, ?)"
        searchtuple = (recipe_id, ingredient_id, ingredient_volume, int(hand_add))
        self.handler.query_database(query, searchtuple)

    def insert_multiple_existing_handadd_ingredients_by_name(self, ingredient_names: List[str]):
        """Insert the IDS of the given ingredient list into the available table"""
        ingredient_id = self.__get_multiple_ingredient_ids_from_names(ingredient_names)
        questionmarks = ",".join(["(?)"] * len(ingredient_id))
        query = f"INSERT INTO Available(ID) VALUES {questionmarks}"
        self.handler.query_database(query, ingredient_id)

    # delete
    def delete_ingredient(self, ingredient_id: int):
        """Deletes an ingredient by id"""
        query = "DELETE FROM Ingredients WHERE ID = ?"
        self.handler.query_database(query, (ingredient_id,))

    def delete_consumption_recipes(self):
        """Sets the resetable consumption of all recipes to zero"""
        query = "UPDATE OR IGNORE Recipes SET Counter = 0"
        self.handler.query_database(query)

    def delete_consumption_ingredients(self):
        """Sets the resetable consumption of all ingredients to zero"""
        query = "UPDATE OR IGNORE Ingredients SET Consumption = 0"
        self.handler.query_database(query)

    def delete_recipe(self, recipe_name: str):
        """Deletes the given recipe by name and all according ingredient_data"""
        # if using FK with cascade delete, this will prob no longer nececary
        query1 = "DELETE FROM RecipeData WHERE Recipe_ID = (SELECT ID FROM Recipes WHERE Name = ?)"
        query2 = "DELETE FROM Recipes WHERE Name = ?"
        self.handler.query_database(query1, (recipe_name,))
        self.handler.query_database(query2, (recipe_name,))

    def delete_recipe_ingredient_data(self, recipe_id: int):
        """Deletes ingredient_data by given ID"""
        query = "DELETE FROM RecipeData WHERE Recipe_ID = ?"
        self.handler.query_database(query, (recipe_id,))

    def delete_existing_handadd_ingredient(self):
        """Deletes all ingredient in the available table"""
        self.handler.query_database("DELETE FROM Available")

    def save_failed_teamdata(self, payload):
        """Saves the failed payload into the db to buffer"""
        self.handler.query_database("INSERT INTO Teamdata(Payload) VALUES(?)", (payload,))

    def get_failed_teamdata(self):
        """Returns one failed teamdata payload"""
        data = self.handler.query_database("SELECT * FROM Teamdata ORDER BY ID ASC LIMIT 1")
        if data:
            return data[0]
        return []

    def delete_failed_teamdata(self, data_id):
        """Deletes the given teamdata by id"""
        self.handler.query_database("DELETE FROM Teamdata WHERE ID=?", (data_id,))


class DatabaseHandler:
    """Handler Class for Connecting and querring Databases"""

    database_path = DIRPATH.parent / f"{DATABASE_NAME}.db"
    database_path_default = DIRPATH.parent / f"{DATABASE_NAME}_default.db"

    def __init__(self):
        self.database_path = DatabaseHandler.database_path
        if not self.database_path_default.exists():
            print("creating Database")
            self.create_tables()
        if not self.database_path.exists():
            print("Copying default database for maker usage")
            self.copy_default_database()
        self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()

    def connect_database(self, path: Optional[str] = None):
        """Connects to the given path or own database and creates cursor"""
        if path:
            self.database = sqlite3.connect(path)
        else:
            self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()

    def query_database(self, sql: str, serachtuple=()):
        """Executes the given querry, if select command, return the data"""
        self.cursor.execute(sql, serachtuple)

        if sql[0:6].lower() == "select":
            result = self.cursor.fetchall()
        else:
            self.database.commit()
            result = []

        return result

    def copy_default_database(self):
        """Creates a local copy of the database"""
        shutil.copy(self.database_path_default, self.database_path)

    def create_tables(self):
        """Creates all needed tables and constraints"""
        self.connect_database(str(self.database_path_default))
        # Creates each Table
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Recipes(
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Name TEXT NOT NULL,
                Alcohol INTEGER NOT NULL,
                Amount INTEGER NOT NULL,
                Comment TEXT,
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
                Hand INTEGER);"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS RecipeData(
                Recipe_ID INTEGER NOT NULL,
                Ingredient_ID INTEGER NOT NULL,
                Amount INTEGER NOT NULL,
                Is_alcoholic INTEGER NOT NULL,
                Hand INTEGER,
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
