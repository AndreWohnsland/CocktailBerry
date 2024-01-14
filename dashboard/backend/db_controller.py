import datetime
from typing import Optional
import sqlite3
from pathlib import Path

DATABASE_NAME = "team"
DIRPATH = Path(__file__).parent.absolute()


class DBController:
    """Controls DB actions"""

    def __init__(self) -> None:
        self.database_path = DIRPATH / "storage" / f"{DATABASE_NAME}.db"
        db_exists = Path(self.database_path).exists()
        self.conn = sqlite3.connect(self.database_path)
        self.cursor = self.conn.cursor()
        if not db_exists:
            print("creating Database")
            self.__create_tables()
        self.__add_person_to_db()

    def __del__(self):
        self.conn.close()

    def enter_cocktail(self, team: str, volume: int, person: Optional[str]):
        if person is None:
            person = "Team"
        sql = "INSERT INTO TEAM(Date, Team, Volume, Person) VALUES(?,?,?,?)"
        entry_datetime = datetime.datetime.now().replace(microsecond=0)
        self.cursor.execute(sql, (entry_datetime, team, volume, person,))
        self.conn.commit()

    def generate_leaderboard(self, hour_range: Optional[int], use_count: bool, limit: int):
        addition = ""
        if hour_range is not None:
            addition = f" WHERE Date >= datetime('now','-{hour_range} hours')"
        agg = self.__count_or_sum(use_count)
        sql = f"SELECT Team, {agg} as amount FROM Team{addition} GROUP BY Team ORDER BY {agg} DESC LIMIT ?"
        self.cursor.execute(sql, (limit,))
        return dict(self.cursor.fetchall())

    def generate_teamdata(self, hour_range: Optional[int], use_count: bool, limit: int):
        addition1 = ""
        addition2 = ""
        if hour_range is not None:
            addition1 = f" WHERE Date >= datetime('now','-{hour_range} hours')"
            addition2 = f" AND Date >= datetime('now','-{hour_range} hours')"
        agg = self.__count_or_sum(use_count)
        sql = f"""SELECT Team, Person, {agg} as amount FROM Team
                WHERE Team in (SELECT Team FROM Team {addition1} GROUP BY Team ORDER BY {agg} DESC LIMIT ?){addition2}
                GROUP BY Team, Person ORDER BY {agg} DESC;
        """
        self.cursor.execute(sql, (limit,))
        return self.cursor.fetchall()

    def __count_or_sum(self, use_count: bool):
        return "count(*)" if use_count else "sum(Volume)"

    def __create_tables(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS
            Team(Date DATETIME NOT NULL,
            Team TEXT NOT NULL,
            Volume INTEGER NOT NULL,
            Person Text);"""
        )
        self.conn.commit()

    def __add_person_to_db(self):
        """Adds the new column to the db"""
        try:
            self.cursor.execute("ALTER TABLE Team ADD Person Text;")
            self.cursor.execute("UPDATE Team SET Person='Team' WHERE Person is Null")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass
