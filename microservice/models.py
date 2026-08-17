from typing import Any

from pydantic import BaseModel


class Cocktail(BaseModel):
    cocktailname: str
    volume: int
    machinename: str
    countrycode: str
    ingredients: list[dict[str, Any]]
    makedate: str | None = None
