import sqlite3
import os
import logging
import time

database_name = "Datenbank"
dirpath = os.path.dirname(__file__)


class DatabaseHandler:
    database_path = os.path.join(dirpath, "..", f"{database_name}.db")

    def __init__(self, create_database=False):
        self.database_path = DatabaseHandler.database_path
        print(self.database_path)
        if create_database:
            self.create_tables()

    def connect_database(self):
        self.database = sqlite3.connect(DatabaseHandler.database_path)
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
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Vorhanden(ID INTEGER NOT NULL);"
        )

        # Creating the Unique Indexes
        self.cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_zutaten_name ON Zutaten(Name)"
        )
        self.cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_rezepte_name ON Rezepte(Name)"
        )
        self.cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_flasche ON Belegung(Flasche)"
        )

        # Creating the Space Naming of the Bottles
        for Flaschen_C in range(1, 13):
            self.cursor.execute(
                "INSERT INTO Belegung(Flasche,Zutat_F) VALUES (?,?)", (Flaschen_C, "")
            )
        self.database.commit()


class LoggerHandler:
    log_folder = os.path.join(dirpath, "..", "logs")

    def __init__(self, loggername, filename):
        self.path = os.path.join(LoggerHandler.log_folder, f"{filename}.log")
        self.logger = logging.getLogger(loggername)
        filehandler = logging.FileHandler(self.path)
        filehandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M")
        filehandler.setFormatter(formatter)
        self.logger.addHandler(filehandler)
        template = "{:-^80}"
        self.logger.debug(template.format("Starting the Programm",))

    def logevent(self, level, message):
        self.logger.log(getattr(logging, level), message)
