from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, TypeVar

from annotated_types import Len
from pydantic import BaseModel, ConfigDict, Field

from src.config.config_manager import StartupIssue
from src.models import Event, OptionTiles, PrepareResult

if TYPE_CHECKING:
    from src.db_models import DbRole, DbWaiter

T = TypeVar("T")


class ErrorDetail(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: PrepareResult
    detail: str
    bottle: int | None = None


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
    is_naturally_virgin: bool
    ingredients: list[CocktailIngredient]
    image: str
    default_image: str


class Ingredient(CocktailIngredient):
    bottle_volume: int
    fill_level: int
    pump_speed: int
    cost: int = 0
    bottle: int | None = None
    disallow_pump_back: bool = False


class IngredientInput(BaseModel):
    name: str
    alcohol: int = Field(..., ge=0)
    bottle_volume: int = Field(..., gt=0)
    fill_level: int = Field(..., ge=0)
    cost: int = Field(..., ge=0)
    pump_speed: int = Field(..., gt=0)
    hand: bool
    unit: str
    disallow_pump_back: bool = False


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


class BottleConfigUpdate(BaseModel):
    volume_flow: float | None = Field(None, gt=0)


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


class UpdateVersion(BaseModel):
    version: str
    release_notes: str
    is_major: bool


class UpdateAvailability(BaseModel):
    status: str
    message: str
    versions: list[UpdateVersion]


class UpdateRequest(BaseModel):
    version: str


class SumupReaderResponse(BaseModel):
    id: str
    name: str


class SumupReaderCreate(BaseModel):
    name: str
    pairing_code: str


PermissionKey = Literal["maker", "ingredients", "recipes", "bottles", "options"]


class TabPermission(BaseModel):
    maker: bool = False
    ingredients: bool = False
    recipes: bool = False
    bottles: bool = False
    options: bool = False


class RoleResponse(BaseModel):
    id: int
    name: str
    permissions: TabPermission
    tile_permissions: OptionTiles

    @classmethod
    def from_db(cls, role: DbRole) -> RoleResponse:
        return cls(
            id=role.id,
            name=role.name,
            permissions=TabPermission(
                maker=role.privilege_maker,
                ingredients=role.privilege_ingredients,
                recipes=role.privilege_recipes,
                bottles=role.privilege_bottles,
                options=role.privilege_options,
            ),
            tile_permissions=OptionTiles(**(role.tile_permissions or {})),
        )


class RoleCreate(BaseModel):
    name: str
    permissions: TabPermission = Field(default_factory=TabPermission)
    tile_permissions: OptionTiles = Field(default_factory=OptionTiles)


class RoleUpdate(BaseModel):
    name: str | None = None
    permissions: TabPermission | None = None
    tile_permissions: OptionTiles | None = None


class WaiterResponse(BaseModel):
    nfc_id: str
    name: str
    role_id: int
    role: RoleResponse
    permissions: TabPermission
    tile_permissions: OptionTiles

    @classmethod
    def from_db(cls, waiter: DbWaiter) -> WaiterResponse:
        role = RoleResponse.from_db(waiter.role)
        return cls(
            nfc_id=waiter.nfc_id,
            name=waiter.name,
            role_id=role.id,
            role=role,
            permissions=role.permissions,
            tile_permissions=role.tile_permissions,
        )


class WaiterCreate(BaseModel):
    nfc_id: str
    name: str
    role_id: int


class WaiterUpdate(BaseModel):
    name: str | None = None
    role_id: int | None = None


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
