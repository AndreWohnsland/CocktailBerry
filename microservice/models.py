from typing import Any, Optional

from pydantic import BaseModel


class Cocktail(BaseModel):
    cocktailname: str
    volume: int
    machinename: str
    countrycode: str
    ingredients: list[dict[str, Any]]
    makedate: Optional[str] = None
