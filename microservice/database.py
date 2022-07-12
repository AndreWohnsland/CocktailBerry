import json
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple

DATABASE_NAME = "failed_data"
DIRPATH = Path(__file__).parent.absolute()


class DatabaseHandler:
    """Handler Class for Connecting and querring Databases"""

    def __init__(self):
        self.database_path = DIRPATH / f"{DATABASE_NAME}.db"
        if not self.database_path.exists():
            print("creating Database")
            self.create_tables()
        self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()
        self.__add_url_to_db()
        self.__add_header_to_db()

    def save_failed_post(self, payload: str, url: str, headers=Dict):
        sql = "INSERT INTO Querry(Payload, Url, Headers) VALUES(?,?,?)"
        self.query_database(sql, (payload, url, json.dumps(headers)))

    def get_failed_data(self) -> List[Tuple[int, str, str, str]]:
        sql = "SELECT * FROM Querry ORDER BY ID ASC"
        return self.query_database(sql)

    def delete_failed_by_id(self, data_id: int):
        sql = "DELETE FROM Querry WHERE ID = ?"
        self.query_database(sql, (data_id,))

    def query_database(self, sql: str, serachtuple=()):
        self.cursor.execute(sql, serachtuple)
        if sql[0:6].lower() == "select":
            result = self.cursor.fetchall()
        else:
            self.database.commit()
            result = []
        return result

    def create_tables(self):
        self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Querry(
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                Payload TEXT NOT NULL,
                Url TEXT NOT NULL);"""
        )
        self.database.commit()
        self.database.close()

    def __add_url_to_db(self):
        """Adds the new column to the db"""
        try:
            self.cursor.execute("ALTER TABLE Querry ADD Url TEXT;")
            self.cursor.execute("DELETE FROM Querry WHERE Url IS NULL")
            self.database.commit()
        except sqlite3.OperationalError:
            pass

    def __add_header_to_db(self):
        try:
            self.cursor.execute("ALTER TABLE Querry ADD Headers TEXT;")
            self.cursor.execute("DELETE FROM Querry WHERE Headers IS NULL")
            self.database.commit()
        except sqlite3.OperationalError:
            pass
