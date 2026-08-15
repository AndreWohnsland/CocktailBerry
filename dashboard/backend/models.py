from pydantic import BaseModel


class TeamInfo(BaseModel):
    team: str
    volume: int
    person: str | None = "Team"
