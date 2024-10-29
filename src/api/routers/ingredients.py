from fastapi import APIRouter, HTTPException

from src.api.models import IngredientInput, map_ingredient
from src.database_commander import DB_COMMANDER as DBC
from src.database_commander import DatabaseTransactionError

router = APIRouter(tags=["ingredients"], prefix="/ingredients")


@router.get("")
async def get_ingredients(machine: bool = True, hand: bool = True):
    ingredients = DBC.get_all_ingredients(get_machine=machine, get_hand=hand)
    return [map_ingredient(i) for i in ingredients]


@router.get("/{ingredient_id}")
async def get_ingredient(ingredient_id: int):
    ingredient = DBC.get_ingredient(ingredient_id)
    return map_ingredient(ingredient)


@router.post("")
async def add_ingredient(ingredient: IngredientInput):
    DBC.insert_new_ingredient(
        ingredient_name=ingredient.name,
        alcohol_level=ingredient.alcohol,
        volume=ingredient.bottle_volume,
        only_hand=ingredient.hand,
        pump_speed=ingredient.pump_speed,
        cost=ingredient.cost,
        unit=ingredient.unit,
    )
    db_ingredient = DBC.get_ingredient(ingredient.name)
    return map_ingredient(db_ingredient)


@router.put("/{ingredient_id}")
async def update_ingredients(ingredient_id: int, ingredient: IngredientInput):
    DBC.set_ingredient_data(
        ingredient_name=ingredient.name,
        alcohol_level=ingredient.alcohol,
        volume=ingredient.bottle_volume,
        new_level=ingredient.fill_level,
        only_hand=ingredient.hand,
        pump_speed=ingredient.pump_speed,
        ingredient_id=ingredient_id,
        cost=ingredient.cost,
        unit=ingredient.unit,
    )
    return {"message": f"Ingredient {ingredient_id} was updated to {ingredient}"}


@router.delete("/{ingredient_id}")
async def delete_ingredients(ingredient_id: int):
    try:
        DBC.delete_ingredient(ingredient_id)
    except DatabaseTransactionError as e:
        raise HTTPException(status_code=406, detail=str(e))
    return {"message": f"Ingredient {ingredient_id} was deleted!"}
