from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, TypeVar

from annotated_types import Len
from pydantic import BaseModel, Field

from src.config.config_manager import StartupIssue
from src.models import Event, PrepareResult

if TYPE_CHECKING:
    from src.db_models import DbWaiter

T = TypeVar("T")


class ErrorDetail(BaseModel):
    status: PrepareResult
    detail: str
    bottle: int | None = None

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
    cocktails: list[Cocktail]
    ingredients: list[Ingredient]


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
    bottle: int | None = None


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
    ingredient: Ingredient | None = None


class PrepareCocktailRequest(BaseModel):
    volume: int = Field(..., gt=0)
    alcohol_factor: float = Field(..., ge=0)
    is_virgin: bool = False
    selected_team: str | None = None
    team_member_name: str | None = None


class WifiData(BaseModel):
    ssid: str
    password: str


class EventsData(BaseModel):
    events: list[Event]
    event_keys: list[str]


class DataResponse[T](BaseModel):
    data: T


class PasswordInput(BaseModel):
    password: int = Field(..., ge=0)


class IssueData(BaseModel):
    deprecated: StartupIssue
    internet: StartupIssue
    config: StartupIssue
    payment: StartupIssue
    waiter: StartupIssue


class DateTimeInput(BaseModel):
    date: str
    time: str


class ApiMessage(BaseModel):
    message: str


class ApiMessageWithData[T](BaseModel):
    message: str
    data: T


class AboutInfo(BaseModel):
    python_version: str
    platform: str
    project_name: str
    version: str


class SumupReaderResponse(BaseModel):
    id: str
    name: str


class SumupReaderCreate(BaseModel):
    name: str
    pairing_code: str


PermissionKey = Literal["maker", "ingredients", "recipes", "bottles", "options"]


class WaiterPermissions(BaseModel):
    maker: bool = False
    ingredients: bool = False
    recipes: bool = False
    bottles: bool = False
    options: bool = False


class WaiterResponse(BaseModel):
    nfc_id: str
    name: str
    permissions: WaiterPermissions

    @classmethod
    def from_db(cls, waiter: DbWaiter) -> WaiterResponse:
        return cls(
            nfc_id=waiter.nfc_id,
            name=waiter.name,
            permissions=WaiterPermissions(
                maker=waiter.privilege_maker,
                ingredients=waiter.privilege_ingredients,
                recipes=waiter.privilege_recipes,
                bottles=waiter.privilege_bottles,
                options=waiter.privilege_options,
            ),
        )


class WaiterCreate(BaseModel):
    nfc_id: str
    name: str
    permissions: WaiterPermissions | None = None


class WaiterUpdate(BaseModel):
    name: str | None = None
    permissions: WaiterPermissions | None = None


class WaiterLogEntry(BaseModel):
    id: int
    timestamp: str
    waiter_name: str
    recipe_name: str
    volume: int
    is_virgin: bool


class CurrentWaiterState(BaseModel):
    nfc_id: str | None = None
    waiter: WaiterResponse | None = None
