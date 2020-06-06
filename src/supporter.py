import sqlite3
import os
import logging
import time
from pathlib import Path

database_name = "Datenbank"
dirpath = os.path.dirname(__file__)


class DatabaseHandler:
    """Handler Class for Connecting and querring Databases"""

    database_path = os.path.join(dirpath, "..", f"{database_name}.db")

    def __init__(self):
        self.database_path = DatabaseHandler.database_path
        print(self.database_path)
        if not Path(self.database_path).exists():
            print("creating Database")
            self.create_tables()

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
            "CREATE TABLE IF NOT EXISTS Rezepte(ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, Name TEXT NOT NULL, Alkoholgehalt INTEGER NOT NULL, Menge INTEGER NOT NULL, Kommentar TEXT, Anzahl_Lifetime INTEGER, Anzahl INTEGER, Enabled INTEGER, V_Alk INTEGER, c_Alk INTEGER, V_Com INTEGER, c_Com INTEGER);"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Zutaten(ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, Name TEXT NOT NULL, Alkoholgehalt INTEGER NOT NULL, Flaschenvolumen INTEGER NOT NULL, Verbrauchsmenge INTEGER, Verbrauch INTEGER, Mengenlevel INTEGER, Hand INTEGER);"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Zusammen(Rezept_ID INTEGER NOT NULL, Zutaten_ID INTEGER NOT NULL, Menge INTEGER NOT NULL, Alkoholisch INTEGER NOT NULL, Hand INTEGER);"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Belegung(Flasche INTEGER NOT NULL, Zutat_F TEXT NOT NULL, ID INTEGER, Mengenlevel INTEGER);"
        )
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Vorhanden(ID INTEGER NOT NULL);")

        # Creating the Unique Indexes
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_zutaten_name ON Zutaten(Name)")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rezepte_name ON Rezepte(Name)")
        self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_flasche ON Belegung(Flasche)")

        # Creating the Space Naming of the Bottles
        for Flaschen_C in range(1, 13):
            self.cursor.execute("INSERT INTO Belegung(Flasche,Zutat_F) VALUES (?,?)", (Flaschen_C, ""))
        self.database.commit()
        self.database.close()


class LoggerHandler:
    """Handler Class for Generating Logger and Logging events"""

    log_folder = os.path.join(dirpath, "..", "logs")

    def __init__(self, loggername, filename):
        self.path = os.path.join(LoggerHandler.log_folder, f"{filename}.log")
        self.logger = logging.getLogger(loggername)
        filehandler = logging.FileHandler(self.path)
        filehandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M")
        filehandler.setFormatter(formatter)
        self.logger.addHandler(filehandler)
        self.TEMPLATE = "{:-^80}"

    def log_event(self, level, message):
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level, message):
        self.log_event(level, self.TEMPLATE.format(message,))

    def log_start_program(self):
        self.logger.debug(self.TEMPLATE.format("Starting the Programm",))


class FieldHandler:
    """Handler Class to evaluate field Values in the UI """

    def __init__(self):
        self.alive = True

    def missing_check(self, lineedits):
        for lineedit in lineedits:
            if lineedit.text() == "":
                return [False, "Es wurde ein Wert vergessen, bitte nachtragen"]
        return [True, None]

    def valid_check_int(self, lineedits, wrongvals):
        for lineedit, wrongval in zip(lineedits, wrongvals):
            try:
                int(lineedit.text())
            except ValueError:
                return [False, f"{wrongval} muss eine Zahl sein"]
        return [True, None]


###### This are temporary Helper Functions, they will be moved later in the UI parent class / there will be objects for them
def generate_CBB_names(w):
    return [getattr(w, f"CBB{x}") for x in range(1, 11)]


def generate_LBelegung_names(w):
    return [getattr(w, f"LBelegung{x}") for x in range(1, 11)]


def generate_PBneu_names(w):
    return [getattr(w, f"PBneu{x}") for x in range(1, 11)]


def generate_ProBBelegung_names(w):
    return [getattr(w, f"ProBBelegung{x}") for x in range(1, 11)]
