import datetime
from pathlib import Path
import sqlite3
from typing import Optional
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

DATABASE_NAME = "team"
DIRPATH = Path(__file__).parent.absolute()
database_path = DIRPATH / "storage" / f"{DATABASE_NAME}.db"

app = FastAPI()


class Teaminfo(BaseModel):
    team: str
    volume: int
    person: Optional[str] = "Team"


class BoardConfig(BaseModel):
    hourrange: Optional[int] = None
    limit: Optional[int] = 5
    count: Optional[bool] = True


@app.get("/")
def home():
    return {"message": "Welcome to dashboard api"}


@app.post("/cocktail")
async def enter_cocktail_for_team(team: Teaminfo):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    entry_datetime = datetime.datetime.now().replace(microsecond=0)
    sql = "INSERT INTO TEAM(Date, Team, Volume, Person) VALUES(?,?,?,?)"
    cursor.execute(sql, (entry_datetime, team.team, team.volume, team.person,))
    conn.commit()
    conn.close()
    return {"message": "Team entry was successfull", "team": team.team, "volume": team.volume, "person": team.person}


def get_leaderboard(hourrange=None, limit=2, count=True):
    addition = ""
    if hourrange is not None:
        addition = f" WHERE Date >= datetime('now','-{hourrange} hours')"
    agg = "count(*)" if count else "sum(Volume)"
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    sql = f"SELECT Team, {agg} as amount FROM Team{addition} GROUP BY Team ORDER BY {agg} DESC LIMIT ?"
    cursor.execute(sql, (limit,))
    return_data = dict(cursor.fetchall())
    conn.close()
    return return_data


@app.get("/leaderboard")
def leaderboard(conf: BoardConfig):
    return get_leaderboard(conf.hourrange, conf.limit, conf.count)


def create_tables():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS
        Team(Date DATETIME NOT NULL,
        Team TEXT NOT NULL,
        Volume INTEGER NOT NULL,
        Person Text);"""
    )
    conn.commit()
    conn.close()


def add_person_to_db():
    """Adds the new column to the db"""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE Team ADD Person Text;")
        cursor.execute("UPDATE Team SET Person='Team' WHERE Person is Null")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()


if __name__ == "__main__":
    if not Path(database_path).exists():
        print("creating Database")
        create_tables()
    # this is new, so add it
    add_person_to_db()
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
