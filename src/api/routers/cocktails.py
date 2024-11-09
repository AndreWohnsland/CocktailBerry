# import asyncio
from typing import Optional

from fastapi import APIRouter

# from sse_starlette.sse import EventSourceResponse
from src.api.internal.utils import calculate_cocktail_volume_and_concentration
from src.api.models import Cocktail, CocktailInput, map_cocktail
from src.config.config_manager import shared
from src.database_commander import DB_COMMANDER as DBC
from src.models import Cocktail as DbCocktail
from src.tabs import maker

router = APIRouter(tags=["cocktails"], prefix="/cocktails")


@router.get("")
async def get_cocktails(only_possible: bool = True, max_hand_add: int = 3):
    cocktails = DBC.get_possible_cocktails(max_hand_add) if only_possible else DBC.get_all_cocktails()
    return [map_cocktail(c) for c in cocktails]


@router.get("/{cocktail_id}")
async def get_cocktail(cocktail_id: int) -> Optional[Cocktail]:
    cocktail = DBC.get_cocktail(cocktail_id)
    return map_cocktail(cocktail)


@router.get("/prepare/{cocktail_id}")
async def prepare_cocktail(cocktail_id: int, volume: int, alcohol_factor: float, is_virgin: bool = False):
    factor = alcohol_factor if not is_virgin else 0
    cocktail = DBC.get_cocktail(cocktail_id)
    if cocktail is None:
        return {"message": f"Cocktail {cocktail_id} not found!"}
    cocktail.scale_cocktail(volume, factor)
    result, msg = maker.prepare_cocktail(cocktail, None)
    return {"message": msg, "result": result.name}

    # # TODO: implement cocktail preparation with sockets
    # # return {"message": f"Cocktail {cocktail} of volume {volume} ({factor}%) prepared successfully!"}
    # async def event_generator():
    #     i = 0
    #     while i < 10:
    #         i += 1
    #         yield f"Cocktail {cocktail} of volume {volume} ({factor}%) {i}/10"
    #         await asyncio.sleep(0.3)
    #     yield "done"

    # return EventSourceResponse(event_generator(), ping=100)


@router.post("/prepare/stop")
async def stop_cocktail():
    shared.make_cocktail = False
    return {"message": "Cocktail preparation stopped!"}


@router.post("")
async def create_cocktail(cocktail: CocktailInput) -> Optional[Cocktail]:
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail = DBC.insert_new_recipe(
        cocktail.name, recipe_alcohol_level, recipe_volume, cocktail.enabled, cocktail.virgin_available, ingredient_data
    )
    return map_cocktail(db_cocktail)


@router.put("/{cocktail_id}")
async def update_cocktail(cocktail_id: int, cocktail: CocktailInput) -> Optional[Cocktail]:
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail: DbCocktail = DBC.set_recipe(
        cocktail_id,
        cocktail.name,
        recipe_alcohol_level,
        recipe_volume,
        cocktail.enabled,
        cocktail.virgin_available,
        ingredient_data,
    )
    return map_cocktail(db_cocktail)


@router.delete("/{cocktail_id}")
async def delete_cocktail(cocktail_id: int):
    DBC.delete_recipe(cocktail_id)
    return {"message": f"Cocktail {cocktail_id} deleted successfully!"}
