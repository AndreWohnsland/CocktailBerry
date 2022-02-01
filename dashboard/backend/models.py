from pydantic import BaseModel
from typing import Optional


class Teaminfo(BaseModel):
    team: str
    volume: int
    person: Optional[str] = "Team"


class BoardConfig(BaseModel):
    hourrange: Optional[int] = None
    limit: Optional[int] = 5
    count: Optional[bool] = True
