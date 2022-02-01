import uvicorn
from fastapi import FastAPI
from models import Teaminfo, BoardConfig
from db_controller import DBController

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Welcome to dashboard api"}


@app.post("/cocktail")
async def enter_cocktail_for_team(team: Teaminfo):
    controller = DBController()
    controller.enter_cocktail(team.team, team.volume, team.person)
    return {"message": "Team entry was successfull", "team": team.team, "volume": team.volume, "person": team.person}


@app.get("/leaderboard")
def leaderboard(conf: BoardConfig):
    controller = DBController()
    return controller.generate_leaderboard(conf.hourrange, conf.count, conf.limit)


@app.get("/teamdata")
def leaderboard(conf: BoardConfig):
    controller = DBController()
    return controller.generate_teamdata(conf.hourrange, conf.count, conf.limit)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
