from typing import Optional

from pydantic import BaseModel

from src.models import Cocktail as DBCocktail
from src.models import Ingredient as DBIngredient


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


class Ingredient(CocktailIngredient):
    bottle_volume: int
    fill_level: int
    pump_speed: int
    cost: int = 0


def map_cocktail(cocktail: Optional[DBCocktail]) -> Optional[Cocktail]:
    if cocktail is None:
        return None
    return Cocktail(
        id=cocktail.id,
        name=cocktail.name,
        alcohol=cocktail.alcohol,
        amount=cocktail.amount,
        enabled=cocktail.enabled,
        virgin_available=cocktail.virgin_available,
        ingredients=[
            CocktailIngredient(
                id=i.id,
                name=i.name,
                alcohol=i.alcohol,
                hand=bool(i.hand),
                amount=i.amount,
                recipe_order=i.recipe_order,
                unit=i.unit,
            )
            for i in cocktail.ingredients
        ],
    )


def map_ingredient(ingredient: Optional[DBIngredient]) -> Optional[Ingredient]:
    if ingredient is None:
        return None
    return Ingredient(
        id=ingredient.id,
        name=ingredient.name,
        alcohol=ingredient.alcohol,
        hand=bool(ingredient.hand),
        amount=ingredient.amount,
        recipe_order=ingredient.recipe_order,
        unit=ingredient.unit,
        bottle_volume=ingredient.bottle_volume,
        fill_level=ingredient.fill_level,
        pump_speed=ingredient.pump_speed,
        cost=ingredient.cost,
    )
