import datetime
import os
from pathlib import Path
import sqlite3

DATABASE_NAME = "Cocktail_database"
DIRPATH = os.path.dirname(__file__)


class DatabaseCommander:
    """Commander Class to execute queries and return the results as lists """

    def __init__(self):
        self.handler = DatabaseHandler()

    def get_recipe_id_by_name(self, recipe_name):
        query = "SELECT ID FROM Rezepte WHERE Name=?"
        value = self.handler.query_database(query, (recipe_name,))
        if not value:
            return 0
        return value[0][0]

    def get_recipe_ingredients_by_id(self, recipe_id):
        query = """SELECT Zutaten.Name, Zusammen.Menge, Zusammen.Hand, Zutaten.ID
                FROM Zusammen INNER JOIN Zutaten ON Zusammen.Zutaten_ID = Zutaten.ID 
                WHERE Zusammen.Rezept_ID = ?"""
        return self.handler.query_database(query, (recipe_id,))

    def get_recipe_ingredients_by_name(self, recipe_name):
        query = """SELECT Zutaten.Name, Zusammen.Menge, Zusammen.Hand, Zutaten.Alkoholgehalt
                FROM Zusammen INNER JOIN Zutaten ON Zutaten.ID = Zusammen.Zutaten_ID 
                WHERE Zusammen.Rezept_ID = (SELECT ID FROM Rezepte WHERE Name = ?)"""
        return self.handler.query_database(query, (recipe_name,))

    def get_recipe_ingredients_with_bottles(self, recipe_name):
        query = """SELECT Zutaten.Name, Zusammen.Menge, Belegung.Flasche, Zusammen.Alkoholisch, Zutaten.Mengenlevel
                FROM Zusammen LEFT JOIN Belegung ON Zusammen.Zutaten_ID = Belegung.ID 
                INNER JOIN Zutaten ON Zutaten.ID = Zusammen.Zutaten_ID 
                WHERE Zusammen.Rezept_ID = (SELECT ID FROM Rezepte WHERE Name =?)"""
        return self.handler.query_database(query, (recipe_name,))

    def get_recipe_handadd_window_properties(self, recipe_name):
        query = """SELECT Z.Zutaten_ID, Z.Menge, Z.Alkoholisch
                FROM Zusammen AS Z 
                INNER JOIN Rezepte AS R ON R.ID = Z.Rezept_ID 
                WHERE R.Name = ? AND Z.Hand = 1"""
        return self.handler.query_database(query, (recipe_name,))

    def get_recipe_ingredients_by_name_seperated_data(self, recipe_name):
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
        query = "SELECT ID, Name, Alkoholgehalt, Menge, Kommentar, Enabled FROM Rezepte"
        return self.handler.query_database(query)

    def build_recipe_object(self):
        recipe_object = {}
        recipe_data = self.get_all_recipes_properties()
        for recipe in recipe_data:
            ingredient_data = self.get_recipe_ingredients_by_id(recipe[0])
            recipe_object[recipe[1]] = {
                "ID": recipe[0],
                "alcohollevel": recipe[2],
                "volume": recipe[3],
                "comment": recipe[4],
                "enabled": recipe[5],
                "ingredients": {a[0]: [a[1], a[2]] for a in ingredient_data},
            }
        return recipe_object

    def get_recipe_ingredients_for_comment(self, recipe_name):
        query = """SELECT Zutaten.Name, Zusammen.Menge, Zutaten.ID, Zusammen.Alkoholisch, Zutaten.Alkoholgehalt
                FROM Zusammen 
                INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID 
                INNER JOIN Zutaten ON Zusammen.Zutaten_ID = Zutaten.ID 
                WHERE Rezepte.Name = ? AND Zusammen.Hand = 1"""
        return self.handler.query_database(query, (recipe_name,))

    def get_enabled_recipes_id(self):
        recipe_data = self.get_all_recipes_properties()
        return [x[0] for x in recipe_data if x[5]]

    def get_disabled_recipes_id(self):
        recipe_data = self.get_all_recipes_properties()
        return [x[0] for x in recipe_data if not x[5]]

    def get_recipes_name(self):
        recipe_data = self.get_all_recipes_properties()
        return [x[1] for x in recipe_data]

    def get_ingredients_at_bottles(self):
        query = "SELECT Zutat_F FROM Belegung"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_ingredients_at_bottles_without_empty_ones(self):
        data = self.get_ingredients_at_bottles()
        return [x for x in data if x != ""]

    def get_ids_at_bottles(self):
        query = "SELECT ID FROM Belegung"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_ingredient_names(self, condition_filter=""):
        query = "SELECT Name FROM Zutaten"
        if condition_filter != "":
            query = f"{query} {condition_filter}"
        names = self.handler.query_database(query)
        return [x[0] for x in names]

    def get_ingredient_names_hand(self):
        return self.get_ingredient_names("WHERE Hand = 1")

    def get_ingredient_names_machine(self):
        return self.get_ingredient_names("WHERE Hand = 0")

    def get_ingredient_name_from_id(self, ingredient_id):
        query = "SELECT Name FROM Zutaten WHERE ID = ?"
        data = self.handler.query_database(query, (ingredient_id,))
        if data:
            return data[0][0]
        return ""

    def get_bottle_fill_levels(self):
        query = """SELECT Zutaten.Mengenlevel, Zutaten.Flaschenvolumen FROM Belegung
                LEFT JOIN Zutaten ON Zutaten.ID = Belegung.ID"""
        values = self.handler.query_database(query)
        levels = []
        for current_value, max_value in values:
            # restrict the value between 0 and 100
            proportion = 0
            if current_value != None:
                proportion = round(min(max(current_value / max_value * 100, 0), 100))
            levels.append(proportion)
        return levels

    def get_ingredient_data(self, ingredient_name):
        query = "SELECT ID, Name, Alkoholgehalt, Flaschenvolumen, Hand, Mengenlevel FROM Zutaten WHERE Name = ?"
        values = self.handler.query_database(query, (ingredient_name,))
        if values:
            values = values[0]
            return {
                "ID": values[0],
                "name": values[1],
                "alcohollevel": values[2],
                "volume": values[3],
                "hand_add": values[4],
                "volume_level": values[5],
            }
        return {}

    def get_bottle_usage(self, ingredient_id):
        query = "SELECT COUNT(*) FROM Belegung WHERE ID = ?"
        if self.handler.query_database(query, (ingredient_id,))[0][0]:
            return True
        return False

    def get_recipe_usage_list(self, ingredient_id):
        query = """SELECT Rezepte.Name FROM Zusammen
                INNER JOIN Rezepte ON Rezepte.ID = Zusammen.Rezept_ID 
                WHERE Zusammen.Zutaten_ID=?"""
        recipe_list = self.handler.query_database(query, (ingredient_id,))
        return [recipe[0] for recipe in recipe_list]

    def get_handadd_ids(self):
        query = "SELECT ID FROM Vorhanden"
        result = self.handler.query_database(query)
        return [x[0] for x in result]

    def get_ingredients_seperated_by_handadd(self, recipe_id):
        handadds = []
        machineadds = []
        ingredients = self.get_recipe_ingredients_by_id(recipe_id)
        for ingredient in ingredients:
            if ingredient[2]:
                handadds.append(ingredient[3])
            else:
                machineadds.append(ingredient[3])
        return handadds, machineadds

    def get_multiple_recipe_names_from_ids(self, id_list):
        questionmarks = ",".join(["?"] * len(id_list))
        query = f"SELECT Name FROM Rezepte WHERE ID in ({questionmarks})"
        result = self.handler.query_database(query, id_list)
        return [x[0] for x in result]

    def get_multiple_ingredient_ids_from_names(self, name_list):
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

    def convert_consumption_data(self, data):
        headers = [row[0] for row in data]
        resetable = [row[1] for row in data]
        lifetime = [row[2] for row in data]
        return [["date", *headers], [datetime.date.today(), *resetable], ["lifetime", *lifetime]]

    def get_enabled_status(self, recipe_name):
        query = "SELECT Enabled FROM Rezepte WHERE Name = ?"
        return self.handler.query_database(query, (recipe_name,))[0]

    def get_available_ingredient_names(self):
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
    def set_bottleorder(self, ingredient_names):
        for i, ingredient in enumerate(ingredient_names):
            bottle = i + 1
            query = """UPDATE OR IGNORE Belegung
                    SET ID = (SELECT ID FROM Zutaten WHERE Name = ?), 
                    Zutat_F = ? 
                    WHERE Flasche = ?"""
            searchtuple = (ingredient, ingredient, bottle)
            self.handler.query_database(query, searchtuple)

    def set_bottle_volumelevel_to_max(self, boolean_list):
        query = """UPDATE OR IGNORE Zutaten
                Set Mengenlevel = Flaschenvolumen
                WHERE ID = (SELECT ID FROM Belegung WHERE Flasche = ?)"""
        for bottle, set_to_max in enumerate(boolean_list, start=1):
            if set_to_max:
                self.handler.query_database(query, (bottle,))

    def set_ingredient_data(self, ingredient_name, alcohollevel, volume, new_level, onlyhand, ingredient_id):
        query = """UPDATE OR IGNORE Zutaten
                SET Name = ?, Alkoholgehalt = ?,
                Flaschenvolumen = ?,
                Mengenlevel = ?,
                Hand = ?
                WHERE ID = ?"""
        searchtuple = (ingredient_name, alcohollevel, volume, new_level, onlyhand, ingredient_id)
        self.handler.query_database(query, searchtuple)

    def set_recipe_counter(self, recipe_name):
        query = """UPDATE OR IGNORE Rezepte
                SET Anzahl_Lifetime = Anzahl_Lifetime + 1, 
                Anzahl = Anzahl + 1 
                WHERE Name = ?"""
        self.handler.query_database(query, (recipe_name,))

    def set_ingredient_consumption(self, ingredient_name, ingredient_consumption):
        query = """UPDATE OR IGNORE Zutaten
                SET Verbrauchsmenge = Verbrauchsmenge + ?, 
                Verbrauch = Verbrauch + ?, 
                Mengenlevel = Mengenlevel - ? 
                WHERE Name = ?"""
        searchtuple = (ingredient_consumption, ingredient_consumption, ingredient_consumption, ingredient_name)
        self.handler.query_database(query, searchtuple)

    def set_multiple_ingredient_consumption(self, ingredient_name_list, ingredient_consumption_list):
        for ingredient_name, ingredient_consumption in zip(ingredient_name_list, ingredient_consumption_list):
            self.set_ingredient_consumption(ingredient_name, ingredient_consumption)

    def set_all_recipes_enabled(self):
        query = "UPDATE OR IGNORE Rezepte SET Enabled = 1"
        self.handler.query_database(query)

    def set_recipe(self, recipe_id, name, alcohollevel, volume, comment, enabled):
        query = """UPDATE OR IGNORE Rezepte
                SET Name = ?, Alkoholgehalt = ?, Menge = ?, Kommentar = ?, Enabled = ?
                WHERE ID = ?"""
        searchtuple = (name, alcohollevel, volume, comment, enabled, recipe_id)
        self.handler.query_database(query, searchtuple)

    def set_ingredient_level_to_value(self, ingredient_id, value):
        query = "UPDATE OR IGNORE Zutaten SET Mengenlevel = ? WHERE ID = ?"
        self.handler.query_database(query, (value, ingredient_id))

    # insert commands
    def insert_new_ingredient(self, ingredient_name, alcohollevel, volume, onlyhand):
        query = """INSERT OR IGNORE INTO
                Zutaten(Name,Alkoholgehalt,Flaschenvolumen,Verbrauchsmenge,Verbrauch,Mengenlevel,Hand) 
                VALUES (?,?,?,0,0,0,?)"""
        searchtuple = (ingredient_name, alcohollevel, volume, onlyhand)
        self.handler.query_database(query, searchtuple)

    def insert_new_recipe(self, name, alcohollevel, volume, comment, enabled):
        query = """INSERT OR IGNORE INTO
                Rezepte(Name, Alkoholgehalt, Menge, Kommentar, Anzahl_Lifetime, Anzahl, Enabled) 
                VALUES (?,?,?,?,0,0,?)"""
        searchtuple = (name, alcohollevel, volume, comment, enabled)
        self.handler.query_database(query, searchtuple)

    def insert_recipe_data(self, recipe_id, ingredient_id, ingredient_volume, isalcoholic, hand_add):
        query = "INSERT OR IGNORE INTO Zusammen(Rezept_ID, Zutaten_ID, Menge, Alkoholisch, Hand) VALUES (?, ?, ?, ?, ?)"
        searchtuple = (recipe_id, ingredient_id, ingredient_volume, isalcoholic, hand_add)
        self.handler.query_database(query, searchtuple)

    def insert_multiple_existing_handadd_ingredients_by_name(self, ingredient_names):
        ingredient_id = self.get_multiple_ingredient_ids_from_names(ingredient_names)
        questionmarks = ",".join(["(?)"] * len(ingredient_id))
        query = f"INSERT INTO Vorhanden(ID) VALUES {questionmarks}"
        self.handler.query_database(query, ingredient_id)

    # delete
    def delete_ingredient(self, ingredient_id):
        query = "DELETE FROM Zutaten WHERE ID = ?"
        self.handler.query_database(query, (ingredient_id,))

    def delete_consumption_recipes(self):
        query = "UPDATE OR IGNORE Rezepte SET Anzahl = 0"
        self.handler.query_database(query)

    def delete_consumption_ingredients(self):
        query = "UPDATE OR IGNORE Zutaten SET Verbrauch = 0"
        self.handler.query_database(query)

    def delete_recipe(self, recipe_name):
        query1 = "DELETE FROM Zusammen WHERE Rezept_ID = (SELECT ID FROM Rezepte WHERE Name = ?)"
        query2 = "DELETE FROM Rezepte WHERE Name = ?"
        self.handler.query_database(query1, (recipe_name,))
        self.handler.query_database(query2, (recipe_name,))

    def delete_recipe_ingredient_data(self, recipe_id):
        query = "DELETE FROM Zusammen WHERE Rezept_ID = ?"
        self.handler.query_database(query, (recipe_id,))

    def delete_existing_handadd_ingredient(self):
        self.handler.query_database(("DELETE FROM Vorhanden"))


class DatabaseHandler:
    """Handler Class for Connecting and querring Databases"""

    database_path = os.path.join(DIRPATH, "..", f"{DATABASE_NAME}.db")

    def __init__(self):
        self.database_path = DatabaseHandler.database_path
        # print(self.database_path)
        if not Path(self.database_path).exists():
            print("creating Database")
            self.create_tables()
        self.database = None
        self.cursor = None

    def connect_database(self):
        self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()

    def query_database(self, sql, serachtuple=()):
        self.connect_database()
        self.cursor.execute(sql, serachtuple)

        if sql[0:6].lower() == "select":
            result = self.cursor.fetchall()
        else:
            self.database.commit()
            result = []

        self.database.close()
        return result

    def create_tables(self):
        self.connect_database()
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
                Zutat_F TEXT NOT NULL,
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
            self.cursor.execute("INSERT INTO Belegung(Flasche,Zutat_F) VALUES (?,?)", (bottle_count, ""))
        self.database.commit()
        self.database.close()
