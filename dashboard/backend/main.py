import os
import datetime
from pathlib import Path
import sqlite3
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

DATABASE_NAME = "team"
DIRPATH = os.path.dirname(__file__)
database_path = os.path.join(DIRPATH, "storage", f"{DATABASE_NAME}.db")

app = FastAPI()


class Teaminfo(BaseModel):
    team: str
    volume: int


@app.get("/")
def home():
    return {"message": "Welcome to dashboard api"}


@app.post("/cocktail")
async def enter_cocktail_for_team(team: Teaminfo):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    entry_datetime = datetime.datetime.now().replace(microsecond=0)
    SQL = "INSERT INTO TEAM(Date, Team, Volume) VALUES(?,?,?)"
    cursor.execute(SQL, (entry_datetime, team.team, team.volume,))
    conn.commit()
    conn.close()
    return {"message": "Team entry was Successfull", "team": team.team, "volume": team.volume}


def create_tables():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS
        Team(Date DATETIME NOT NULL,
        Team TEXT NOT NULL,
        Volume INTEGER NOT NULL);"""
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    if not Path(database_path).exists():
        print("creating Database")
        create_tables()
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
