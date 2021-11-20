import os
from pathlib import Path
import sqlite3

DATABASE_NAME = "failed_data"
DIRPATH = os.path.dirname(os.path.abspath(__file__))


class DatabaseHandler:
    """Handler Class for Connecting and querring Databases"""

    def __init__(self):
        self.database_path = os.path.join(DIRPATH, f"{DATABASE_NAME}.db")
        if not Path(self.database_path).exists():
            print("creating Database")
            self.create_tables()
        self.database = sqlite3.connect(self.database_path)
        self.cursor = self.database.cursor()

    def save_failed_post(self, payload: str):
        sql = "INSERT INTO Querry(Payload) VALUES(?)"
        self.query_database(sql, (payload,))

    def get_failed_data(self):
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
                Payload TEXT NOT NULL);"""
        )
        self.database.commit()
        self.database.close()
