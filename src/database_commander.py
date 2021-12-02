import datetime
import os
import shutil
from pathlib import Path
import sqlite3
from typing import Dict, List, Union

from src.models import Cocktail, Ingredient, IngredientData

DATABASE_NAME = "Cocktail_database"
DIRPATH = os.path.dirname(os.path.abspath(__file__))


class DatabaseCommander:
    """Commander Class to execute queries and return the results as lists """

    def __init__(self):
        self.handler = DatabaseHandler()

    def get_recipe_id_by_name(self, recipe_name: str) -> int:
        """Returns the recipe ID for the given name"""
        query = "SELECT ID FROM Rezepte WHERE Name=?"
        value = self.handler.query_database(query, (recipe_name,))
        if not value:
            return 0
        return value[0][0]

    def get_recipe_ingredients_by_id(self, recipe_id: int):
        """Return ingredient data for recipe from recipe ID"""
        query = """SELECT Zutaten.Name, Zusammen.Menge, Zusammen.Hand, Zutaten.ID, Zutaten.Alkoholgehalt
                FROM Zusammen INNER JOIN Zutaten ON Zusammen.Zutaten_ID = Zutaten.ID 
                WHERE Zusammen.Rezept_ID = ?"""
        return self.handler.query_database(query, (recipe_id,))

    def get_recipe_ingredients_by_name(self, recipe_name: str):
        """Return ingredient data for recipe from recipe name"""
        query = """SELECT Zutaten.Name, Zusammen.Menge, Zusammen.Hand, Zutaten.Alkoholgehalt
                FROM Zusammen INNER JOIN Zutaten ON Zutaten.ID = Zusammen.Zutaten_ID 
                WHERE Zusammen.Rezept_ID = (SELECT ID FROM Rezepte WHERE Name = ?)"""
        return self.handler.query_database(query, (recipe_name,))

    def get_recipe_ingredients_with_bottles(self, recipe_name: str):
        """Return the recipe data needed for cocktail making process for given name"""
        query = """SELECT Zutaten.Name, Zusammen.Menge, Belegung.Flasche, Zusammen.Alkoholisch, Zutaten.Mengenlevel
                FROM Zusammen LEFT JOIN Belegung ON Zusammen.Zutaten_ID = Belegung.ID 
                INNER JOIN Zutaten ON Zutaten.ID = Zusammen.Zutaten_ID 
                WHERE Zusammen.Rezept_ID = (SELECT ID FROM Rezepte WHERE Name =?)"""
        return self.handler.query_database(query, (recipe_name,))

    def get_recipe_ingredients_by_name_seperated_data(self, recipe_name: str):
        """Return recipe ingredients as two list for machine add and hand add for a given name"""
        data = self.get_recipe_ingredients_by_name(recipe_name)
        handadd_data = []
        machineaddd_data = []
        for row in data:
            if row[2]:
                handadd_data.append(row[0:2])
            else:
                machineaddd_data.append(row[0:2])
        return machineaddd_data, handadd_data

    def get_all_recipes_properties(self):
        """Get all neeeded data for all recipes"""
        query = "SELECT ID, Name, Alkoholgehalt, Menge, Kommentar, Enabled FROM Rezepte"
        return self.handler.query_database(query)

    def build_cocktail(self, recipe_id: int, name: str, alcohol: int, amount: int, comment: str, enabled: bool):
        """Build one cocktail object with the given data"""
        ingredient_data = self.get_recipe_ingredients_by_id(recipe_id)
        return Cocktail(
            recipe_id, name, alcohol, amount, comment, bool(enabled),
            [IngredientData(ing[3], ing[0], ing[4], ing[1], bool(ing[2])) for ing in ingredient_data]
        )

    # TODO: use this object in further code for better code usage
    def build_cocktail_dict(self) -> Dict[str, Cocktail]:
        """Bilds a dict of all cocktails with name as key and object as value"""
        cocktails = {}
        recipe_data = self.get_all_recipes_properties()
        for recipe in recipe_data:
            cocktails[recipe[1]] = self.build_cocktail(*recipe)
        return cocktails

    def get_cocktail(self, search: Union[str, int]) -> Union[Cocktail, None]:
        """Get all neeeded data for the cocktail from ID or name"""
        if isinstance(search, str):
            condition = "Name"
        else:
            condition = "ID"
        query = f"SELECT ID, Name, Alkoholgehalt, Menge, Kommentar, Enabled FROM Rezepte WHERE {condition}=?"
        data = self.handler.query_database(query, (search,))
        # returns None if no data exists
        if not data:
            return None
        recipe = data[0]
        return self.build_cocktail(*recipe)

    def get_recipe_ingredients_for_comment(self, recipe_name: str):
        """Return data for handadd"""
        query = """SELECT Zutaten.Name, Zusammen.Menge, Zutaten.ID, Zusammen.Alkoholisch, Zutaten.Alkoholgehalt
                FROM Zusammen 
                INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID 
                INNER JOIN Zutaten ON Zusammen.Zutaten_ID = Zutaten.ID 
                WHERE Rezepte.Name = ? AND Zusammen.Hand = 1"""
        return self.handler.query_database(query, (recipe_name,))

    def get_enabled_recipes_id(self) -> List[int]:
        """Return id of enabled recipes"""
        recipe_data = self.get_all_recipes_properties()
        return [x[0] for x in recipe_data if x[5]]

    def get_disabled_recipes_id(self) -> List[int]:
        """Return id of disabled recipes"""
        recipe_data = self.get_all_recipes_properties()
        return [x[0] for x in recipe_data if not x[5]]

    def get_recipes_name(self) -> List[str]:
        """Return names of all recipes"""
        recipe_data = self.get_all_recipes_properties()
        return [x[1] for x in recipe_data]

    def get_ingredients_at_bottles(self) -> List[str]:
        """Return ingredient name for all bottles"""
        query = """SELECT Zutaten.Name FROM Belegung
                    LEFT JOIN Zutaten ON
                    Zutaten.ID=Belegung.ID
                    ORDER BY Belegung.Flasche"""
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_ingredients_at_bottles_without_empty_ones(self) -> List[str]:
        """Return ingredient name for all bottles without empty bottles"""
        data = self.get_ingredients_at_bottles()
        return [x for x in data if x != ""]

    def get_ids_at_bottles(self) -> List[int]:
        """Return all ingredient ids from bottles"""
        query = "SELECT ID FROM Belegung"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_ingredient_names(self, condition_filter="") -> List[str]:
        """Return all ingredient names, option to set a where condition"""
        query = "SELECT Name FROM Zutaten"
        if condition_filter != "":
            query = f"{query} {condition_filter}"
        names = self.handler.query_database(query)
        return [x[0] for x in names]

    def get_ingredient_names_hand(self) -> List[str]:
        """Return all ingredient names, where hand is true"""
        return self.get_ingredient_names("WHERE Hand = 1")

    def get_ingredient_names_machine(self) -> List[str]:
        """Return all ingredient names, where hand is false"""
        return self.get_ingredient_names("WHERE Hand = 0")

    def get_ingredient_name_from_id(self, ingredient_id: int) -> str:
        """Return the according ingredient name from an ID"""
        query = "SELECT Name FROM Zutaten WHERE ID = ?"
        data = self.handler.query_database(query, (ingredient_id,))
        if data:
            return data[0][0]
        return ""

    def get_bottle_fill_levels(self) -> List[int]:
        """Returns percentage of fill level, limited to [0, 100]"""
        query = """SELECT Zutaten.Mengenlevel, Zutaten.Flaschenvolumen FROM Belegung
                LEFT JOIN Zutaten ON Zutaten.ID = Belegung.ID"""
        values = self.handler.query_database(query)
        levels = []
        for current_value, max_value in values:
            # restrict the value between 0 and 100
            proportion = 0
            if current_value is not None:
                proportion = round(min(max(current_value / max_value * 100, 0), 100))
            levels.append(proportion)
        return levels

    def build_ingredient(self, ing_id: int, name: str, alcohol: int, volume: int, fill: int, hand: bool):
        return Ingredient(ing_id, name, alcohol, volume, fill, hand)

    def get_ingredient(self, search: Union[str, int]) -> Union[Ingredient, None]:
        """Get all neeeded data for the ingredient from ID or name"""
        if isinstance(search, str):
            condition = "Name"
        else:
            condition = "ID"
        query = f"SELECT ID, Name, Alkoholgehalt, Flaschenvolumen, Mengenlevel, Hand FROM Zutaten WHERE {condition}=?"
        data = self.handler.query_database(query, (search,))
        # returns None if no data exists
        if not data:
            return None
        ingredient = data[0]
        return Ingredient(*ingredient)

    def get_bottle_usage(self, ingredient_id: int):
        query = "SELECT COUNT(*) FROM Belegung WHERE ID = ?"
        if self.handler.query_database(query, (ingredient_id,))[0][0]:
            return True
        return False

    def get_recipe_usage_list(self, ingredient_id: int) -> List[str]:
        query = """SELECT Rezepte.Name FROM Zusammen
                INNER JOIN Rezepte ON Rezepte.ID = Zusammen.Rezept_ID 
                WHERE Zusammen.Zutaten_ID=?"""
        recipe_list = self.handler.query_database(query, (ingredient_id,))
        return [recipe[0] for recipe in recipe_list]

    def get_handadd_ids(self) -> List[int]:
        query = "SELECT ID FROM Vorhanden"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_ingredients_seperated_by_handadd(self, recipe_id: int):
        handadds = []
        machineadds = []
        ingredients = self.get_recipe_ingredients_by_id(recipe_id)
        for ingredient in ingredients:
            if ingredient[2]:
                handadds.append(ingredient[3])
            else:
                machineadds.append(ingredient[3])
        return handadds, machineadds

    def get_multiple_recipe_names_from_ids(self, id_list: List[int]) -> List[str]:
        questionmarks = ",".join(["?"] * len(id_list))
        query = f"SELECT Name FROM Rezepte WHERE ID in ({questionmarks})"
        result = self.handler.query_database(query, id_list)
        return [x[0] for x in result]

    def get_multiple_ingredient_ids_from_names(self, name_list: List[str]) -> List[int]:
        questionmarks = ",".join(["?"] * len(name_list))
        query = f"SELECT ID FROM Zutaten WHERE Name in ({questionmarks})"
        result = self.handler.query_database(query, name_list)
        return [x[0] for x in result]

    def get_consumption_data_lists_recipes(self):
        query = "SELECT Name, Anzahl, Anzahl_Lifetime FROM Rezepte"
        data = self.handler.query_database(query)
        return self.convert_consumption_data(data)

    def get_consumption_data_lists_ingredients(self):
        query = "SELECT Name, Verbrauch, Verbrauchsmenge FROM Zutaten"
        data = self.handler.query_database(query)
        return self.convert_consumption_data(data)

    def convert_consumption_data(self, data: List[List]):
        headers = [row[0] for row in data]
        resetable = [row[1] for row in data]
        lifetime = [row[2] for row in data]
        return [["date", *headers], [datetime.date.today(), *resetable], ["lifetime", *lifetime]]

    def get_enabled_status(self, recipe_name: str) -> int:
        query = "SELECT Enabled FROM Rezepte WHERE Name = ?"
        return self.handler.query_database(query, (recipe_name,))[0][0]

    def get_available_ingredient_names(self) -> List[str]:
        query = """SELECT Zutaten.Name FROM Zutaten
                INNER JOIN Vorhanden ON Vorhanden.ID = Zutaten.ID"""
        data = self.handler.query_database(query)
        return [x[0] for x in data]

    def get_bottle_data_bottle_window(self):
        query = """SELECT Zutaten.Name, Zutaten.Mengenlevel, Zutaten.ID, Zutaten.Flaschenvolumen
                FROM Belegung LEFT JOIN Zutaten ON Zutaten.ID = Belegung.ID ORDER BY Belegung.Flasche"""
        return self.handler.query_database(query)

    def get_ingredient_bottle_and_level_by_name(self, ingredient_name):
        query = """SELECT Belegung.Flasche, Zutaten.Mengenlevel
                FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID
                WHERE Zutaten.Name = ?"""
        data = self.handler.query_database(query, (ingredient_name,))
        if data:
            return data[0][0], data[0][1]
        return 0, 0

    # set (update) commands
    def set_bottleorder(self, ingredient_names: List[str]):
        for i, ingredient in enumerate(ingredient_names):
            bottle = i + 1
            query = """UPDATE OR IGNORE Belegung
                    SET ID = (SELECT ID FROM Zutaten WHERE Name = ?)
                    WHERE Flasche = ?"""
            searchtuple = (ingredient, bottle)
            self.handler.query_database(query, searchtuple)

    def set_bottle_volumelevel_to_max(self, boolean_list: List[bool]):
        query = """UPDATE OR IGNORE Zutaten
                Set Mengenlevel = Flaschenvolumen
                WHERE ID = (SELECT ID FROM Belegung WHERE Flasche = ?)"""
        for bottle, set_to_max in enumerate(boolean_list, start=1):
            if set_to_max:
                self.handler.query_database(query, (bottle,))

    def set_ingredient_data(self, ingredient_name: str, alcohollevel: int, volume: int, new_level: int, onlyhand: int, ingredient_id: int):
        query = """UPDATE OR IGNORE Zutaten
                SET Name = ?, Alkoholgehalt = ?,
                Flaschenvolumen = ?,
                Mengenlevel = ?,
                Hand = ?
                WHERE ID = ?"""
        searchtuple = (ingredient_name, alcohollevel, volume, new_level, onlyhand, ingredient_id)
        self.handler.query_database(query, searchtuple)

    def set_recipe_counter(self, recipe_name: str):
        query = """UPDATE OR IGNORE Rezepte
                SET Anzahl_Lifetime = Anzahl_Lifetime + 1, 
                Anzahl = Anzahl + 1 
                WHERE Name = ?"""
        self.handler.query_database(query, (recipe_name,))

    def set_ingredient_consumption(self, ingredient_name: str, ingredient_consumption: int):
        query = """UPDATE OR IGNORE Zutaten
                SET Verbrauchsmenge = Verbrauchsmenge + ?, 
                Verbrauch = Verbrauch + ?, 
                Mengenlevel = Mengenlevel - ? 
                WHERE Name = ?"""
        searchtuple = (ingredient_consumption, ingredient_consumption, ingredient_consumption, ingredient_name)
        self.handler.query_database(query, searchtuple)

    def set_multiple_ingredient_consumption(self, ingredient_name_list: List[str], ingredient_consumption_list: List[int]):
        for ingredient_name, ingredient_consumption in zip(ingredient_name_list, ingredient_consumption_list):
            self.set_ingredient_consumption(ingredient_name, ingredient_consumption)

    def set_all_recipes_enabled(self):
        query = "UPDATE OR IGNORE Rezepte SET Enabled = 1"
        self.handler.query_database(query)

    def set_recipe(self, recipe_id: int, name: str, alcohollevel: int, volume: int, comment: str, enabled: int):
        query = """UPDATE OR IGNORE Rezepte
                SET Name = ?, Alkoholgehalt = ?, Menge = ?, Kommentar = ?, Enabled = ?
                WHERE ID = ?"""
        searchtuple = (name, alcohollevel, volume, comment, enabled, recipe_id)
        self.handler.query_database(query, searchtuple)

    def set_ingredient_level_to_value(self, ingredient_id: int, value: int):
        query = "UPDATE OR IGNORE Zutaten SET Mengenlevel = ? WHERE ID = ?"
        self.handler.query_database(query, (value, ingredient_id))

    # insert commands
    def insert_new_ingredient(self, ingredient_name: str, alcohollevel: int, volume: int, onlyhand: int):
        query = """INSERT OR IGNORE INTO
                Zutaten(Name,Alkoholgehalt,Flaschenvolumen,Verbrauchsmenge,Verbrauch,Mengenlevel,Hand) 
                VALUES (?,?,?,0,0,0,?)"""
        searchtuple = (ingredient_name, alcohollevel, volume, onlyhand)
        self.handler.query_database(query, searchtuple)

    def insert_new_recipe(self, name: str, alcohollevel: int, volume: int, comment: str, enabled: int):
        query = """INSERT OR IGNORE INTO
                Rezepte(Name, Alkoholgehalt, Menge, Kommentar, Anzahl_Lifetime, Anzahl, Enabled) 
                VALUES (?,?,?,?,0,0,?)"""
        searchtuple = (name, alcohollevel, volume, comment, enabled)
        self.handler.query_database(query, searchtuple)

    def insert_recipe_data(self, recipe_id: int, ingredient_id: int, ingredient_volume: int, isalcoholic: int, hand_add: int):
        query = "INSERT OR IGNORE INTO Zusammen(Rezept_ID, Zutaten_ID, Menge, Alkoholisch, Hand) VALUES (?, ?, ?, ?, ?)"
        searchtuple = (recipe_id, ingredient_id, ingredient_volume, isalcoholic, hand_add)
        self.handler.query_database(query, searchtuple)

    def insert_multiple_existing_handadd_ingredients_by_name(self, ingredient_names: List[str]):
        ingredient_id = self.get_multiple_ingredient_ids_from_names(ingredient_names)
        questionmarks = ",".join(["(?)"] * len(ingredient_id))
        query = f"INSERT INTO Vorhanden(ID) VALUES {questionmarks}"
        self.handler.query_database(query, ingredient_id)

    # delete
    def delete_ingredient(self, ingredient_id: int):
        query = "DELETE FROM Zutaten WHERE ID = ?"
        self.handler.query_database(query, (ingredient_id,))

    def delete_consumption_recipes(self):
        query = "UPDATE OR IGNORE Rezepte SET Anzahl = 0"
        self.handler.query_database(query)

    def delete_consumption_ingredients(self):
        query = "UPDATE OR IGNORE Zutaten SET Verbrauch = 0"
        self.handler.query_database(query)

    def delete_recipe(self, recipe_name: str):
        query1 = "DELETE FROM Zusammen WHERE Rezept_ID = (SELECT ID FROM Rezepte WHERE Name = ?)"
        query2 = "DELETE FROM Rezepte WHERE Name = ?"
        self.handler.query_database(query1, (recipe_name,))
        self.handler.query_database(query2, (recipe_name,))

    def delete_recipe_ingredient_data(self, recipe_id: int):
        query = "DELETE FROM Zusammen WHERE Rezept_ID = ?"
        self.handler.query_database(query, (recipe_id,))

    def delete_existing_handadd_ingredient(self):
        self.handler.query_database(("DELETE FROM Vorhanden"))


class DatabaseHandler:
    """Handler Class for Connecting and querring Databases"""

    database_path = os.path.join(DIRPATH, "..", f"{DATABASE_NAME}.db")
    database_path_default = os.path.join(DIRPATH, "..", f"{DATABASE_NAME}_default.db")

    def __init__(self):
        self.database_path = DatabaseHandler.database_path
        if not Path(self.database_path_default).exists():
            print("creating Database")
            self.create_tables()
        if not Path(self.database_path).exists():
            print("Copying default database for maker usage")
            self.copy_default_database()
        self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()

    def connect_database(self, path: str = None):
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
        self.connect_database(self.database_path_default)
        # Creates each Table
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Rezepte(
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Name TEXT NOT NULL,
                Alkoholgehalt INTEGER NOT NULL,
                Menge INTEGER NOT NULL,
                Kommentar TEXT,
                Anzahl_Lifetime INTEGER,
                Anzahl INTEGER,
                Enabled INTEGER);"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Zutaten(
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Name TEXT NOT NULL,
                Alkoholgehalt INTEGER NOT NULL,
                Flaschenvolumen INTEGER NOT NULL,
                Verbrauchsmenge INTEGER,
                Verbrauch INTEGER,
                Mengenlevel INTEGER,
                Hand INTEGER);"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Zusammen(
                Rezept_ID INTEGER NOT NULL,
                Zutaten_ID INTEGER NOT NULL,
                Menge INTEGER NOT NULL,
                Alkoholisch INTEGER NOT NULL,
                Hand INTEGER,
                CONSTRAINT fk_zusammen_zutat
                    FOREIGN KEY (Zutaten_ID)
                    REFERENCES Zutaten (ID)
                    ON DELETE RESTRICT,
                CONSTRAINT fk_zusammen_rezept
                    FOREIGN KEY (Rezept_ID)
                    REFERENCES Rezepte (ID)
                    ON DELETE CASCADE
                );"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Belegung(
                Flasche INTEGER NOT NULL,
                ID INTEGER,
                CONSTRAINT fk_belegung_zutat
                    FOREIGN KEY (ID)
                    REFERENCES Zutaten (ID)
                    ON DELETE RESTRICT
                );"""
        )
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Vorhanden(ID INTEGER NOT NULL);")

        # Creating the Unique Indexes
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_zutaten_name ON Zutaten(Name)")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rezepte_name ON Rezepte(Name)")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_flasche ON Belegung(Flasche)")

        # Creating the Space Naming of the Bottles
        for bottle_count in range(1, 13):
            self.cursor.execute("INSERT INTO Belegung(Flasche) VALUES (?)", (bottle_count))
        self.database.commit()
        self.database.close()


DB_COMMANDER = DatabaseCommander()
