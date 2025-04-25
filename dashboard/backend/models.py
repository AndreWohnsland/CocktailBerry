from typing import Optional

from pydantic import BaseModel


class TeamInfo(BaseModel):
    team: str
    volume: int
    person: Optional[str] = "Team"
