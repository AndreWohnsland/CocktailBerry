from typing import Annotated, Generic, Optional, TypeVar

from annotated_types import Len
from pydantic import BaseModel, Field

from src.models import PrepareResult

T = TypeVar("T")


class ErrorDetail(BaseModel):
    status: PrepareResult
    detail: str


class CocktailStatus(BaseModel):
    progress: int = 0
    completed: bool = False
    message: Optional[str] = None
    status: PrepareResult = PrepareResult.FINISHED


class CocktailIngredient(BaseModel):
    id: int
    name: str
    alcohol: int
    hand: bool
    amount: int = 0
    recipe_order: int = 1
    unit: str = "ml"


class Cocktail(BaseModel):
    id: int
    name: str
    alcohol: int
    amount: int
    enabled: bool
    virgin_available: bool
    ingredients: list[CocktailIngredient]
    image: str
    default_image: str


class Ingredient(CocktailIngredient):
    bottle_volume: int
    fill_level: int
    pump_speed: int
    cost: int = 0


class IngredientInput(BaseModel):
    name: str
    alcohol: int
    bottle_volume: int
    fill_level: int
    cost: int
    pump_speed: int
    hand: bool
    unit: str


class CocktailIngredientInput(BaseModel):
    id: int
    amount: int
    recipe_order: int


class CocktailInput(BaseModel):
    name: str
    enabled: bool
    virgin_available: bool
    ingredients: Annotated[list[CocktailIngredientInput], Len(min_length=1)]


class Bottle(BaseModel):
    number: int
    ingredient: Optional[Ingredient]


class PrepareCocktailRequest(BaseModel):
    volume: int = Field(..., gt=0)
    alcohol_factor: float
    is_virgin: bool = False


class DataResponse(BaseModel, Generic[T]):
    data: T
