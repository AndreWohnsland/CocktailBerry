from pydantic import BaseModel
from typing import Optional


class TeamInfo(BaseModel):
    team: str
    volume: int
    person: Optional[str] = "Team"
