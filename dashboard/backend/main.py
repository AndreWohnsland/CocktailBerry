from typing import Optional

import uvicorn
from db_controller import DBController
from fastapi import FastAPI

from models import TeamInfo

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Welcome to dashboard api"}


@app.post("/cocktail")
async def enter_cocktail_for_team(team: TeamInfo):
    controller = DBController()
    controller.enter_cocktail(team.team, team.volume, team.person)
    return {"message": "Team entry was successful", "team": team.team, "volume": team.volume, "person": team.person}


@app.get("/leaderboard")
def leaderboard(hour_range: Optional[int] = None, limit: int = 5, count: bool = True):
    controller = DBController()
    return controller.generate_leaderboard(hour_range, count, limit)


@app.get("/teamdata")
def teamdata(hour_range: Optional[int] = None, limit: int = 5, count: bool = True):
    controller = DBController()
    return controller.generate_teamdata(hour_range, count, limit)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
