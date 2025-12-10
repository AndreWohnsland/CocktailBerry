from typing import Annotated, Generic, Optional, TypeVar

from annotated_types import Len
from pydantic import BaseModel, Field

from src.config.config_manager import StartupIssue
from src.models import PrepareResult

T = TypeVar("T")


class ErrorDetail(BaseModel):
    status: PrepareResult
    detail: str
    bottle: Optional[int] = None

    class Config:  # noqa: D106
        use_enum_values = True


class CocktailIngredient(BaseModel):
    id: int
    name: str
    alcohol: int
    hand: bool
    amount: int = 0
    recipe_order: int = 1
    unit: str = "ml"


class CocktailsAndIngredients(BaseModel):
    cocktails: list["Cocktail"]
    ingredients: list["Ingredient"]


class Cocktail(BaseModel):
    id: int
    name: str
    alcohol: int
    amount: int
    price_per_100_ml: float
    enabled: bool
    is_allowed: bool
    virgin_available: bool
    only_virgin: bool
    ingredients: list[CocktailIngredient]
    image: str
    default_image: str


class Ingredient(CocktailIngredient):
    bottle_volume: int
    fill_level: int
    pump_speed: int
    cost: int = 0
    bottle: Optional[int] = None


class IngredientInput(BaseModel):
    name: str
    alcohol: int = Field(..., ge=0)
    bottle_volume: int = Field(..., gt=0)
    fill_level: int = Field(..., ge=0)
    cost: int = Field(..., ge=0)
    pump_speed: int = Field(..., gt=0)
    hand: bool
    unit: str


class CocktailIngredientInput(BaseModel):
    id: int
    amount: int = Field(..., gt=0)
    recipe_order: int = Field(..., gt=0)


class CocktailInput(BaseModel):
    name: str
    enabled: bool
    price_per_100_ml: float = Field(..., ge=0)
    virgin_available: bool
    ingredients: Annotated[list[CocktailIngredientInput], Len(min_length=1)]


class Bottle(BaseModel):
    number: int
    ingredient: Optional[Ingredient]


class PrepareCocktailRequest(BaseModel):
    volume: int = Field(..., gt=0)
    alcohol_factor: float = Field(..., ge=0)
    is_virgin: bool = False
    selected_team: Optional[str] = None
    team_member_name: Optional[str] = None


class WifiData(BaseModel):
    ssid: str
    password: str


class DataResponse(BaseModel, Generic[T]):
    data: T


class PasswordInput(BaseModel):
    password: int = Field(..., ge=0)


class IssueData(BaseModel):
    deprecated: StartupIssue
    internet: StartupIssue
    config: StartupIssue


class DateTimeInput(BaseModel):
    date: str
    time: str


class ApiMessage(BaseModel):
    message: str


class ApiMessageWithData(BaseModel, Generic[T]):
    message: str
    data: T
