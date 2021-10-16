import os
import datetime
from pathlib import Path
import sqlite3
from typing import Optional
import pandas as pd
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


def get_leaderboard(hourrange=None, limit=2, count=True):
    addition = ""
    if hourrange is not None:
        addition = f" WHERE Date >= datetime('now','-{hourrange} hours')"
    agg = "count(*)" if count else "sum(Volume)"
    conn = sqlite3.connect(database_path)
    SQL = f"SELECT Team, {agg} as amount FROM Team{addition} GROUP BY Team ORDER BY {agg} DESC LIMIT ?"
    df = pd.read_sql(SQL, conn, params=(limit,))
    conn.close()
    return_data = {x: y for x, y in zip(df.Team.to_list(), df.amount.to_list())}
    return return_data


@app.get("/leaderboard")
def leaderboard(
    hourrange: Optional[int] = 24,
    limit: Optional[int] = 5,
    count: Optional[bool] = True
):
    return get_leaderboard(hourrange, limit, count)


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
