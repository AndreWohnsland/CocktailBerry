from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from src.api.internal.utils import map_ingredient
from src.api.models import ErrorDetail, IngredientInput
from src.database_commander import DatabaseCommander
from src.dialog_handler import DialogHandler
from src.models import Cocktail, CocktailStatus, PrepareResult
from src.tabs import maker

router = APIRouter(tags=["ingredients"], prefix="/ingredients")
_dialog_handler = DialogHandler()


@router.get("")
async def get_ingredients(machine: bool = True, hand: bool = True):
    DBC = DatabaseCommander()
    ingredients = DBC.get_all_ingredients(get_machine=machine, get_hand=hand)
    return [map_ingredient(i) for i in ingredients]


@router.get("/{ingredient_id:int}")
async def get_ingredient(ingredient_id: int):
    DBC = DatabaseCommander()
    ingredient = DBC.get_ingredient(ingredient_id)
    return map_ingredient(ingredient)


@router.post("")
async def add_ingredient(ingredient: IngredientInput):
    DBC = DatabaseCommander()
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


@router.put("/{ingredient_id:int}")
async def update_ingredients(ingredient_id: int, ingredient: IngredientInput):
    DBC = DatabaseCommander()
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


@router.delete("/{ingredient_id:int}")
async def delete_ingredients(ingredient_id: int):
    DBC = DatabaseCommander()
    DBC.delete_ingredient(ingredient_id)
    return {"message": f"Ingredient {ingredient_id} was deleted!"}


@router.get("/available")
async def get_available_ingredients() -> list[int]:
    DBC = DatabaseCommander()
    return DBC.get_available_ids()


@router.post("/available")
async def post_available_ingredients(available: list[int]):
    DBC = DatabaseCommander()
    DBC.delete_existing_handadd_ingredient()
    DBC.insert_multiple_existing_handadd_ingredients(available)
    return {"message": "Ingredients were updated!"}


@router.post(
    "/{ingredient_id:int}/prepare",
    tags=["preparation"],
    responses={
        200: {"description": "Ingredient preparation started", "model": CocktailStatus},
        400: {"description": "Validation error", "model": ErrorDetail},
        404: {
            "description": "Ingredient not found",
            "content": {"application/json": {"example": {"detail": "Ingredient not found"}}},
        },
    },
)
async def prepare_ingredient(ingredient_id: int, amount: int, background_tasks: BackgroundTasks):
    DBC = DatabaseCommander()
    ingredient = DBC.get_ingredient(ingredient_id)
    if ingredient is None:
        message = _dialog_handler.get_translation("element_not_found", element_name=f"Ingredient (id={ingredient_id})")
        raise HTTPException(status_code=404, detail=message)
    if ingredient.hand:
        raise HTTPException(
            status_code=400,
            detail="Hand add ingredient cannot be prepared!",
        )
    ingredient.amount = amount
    cocktail = Cocktail(0, ingredient.name, 0, amount, True, True, [ingredient])
    result, message = maker.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        return JSONResponse(status_code=400, content={"status": result.value, "detail": message})
    background_tasks.add_task(maker.prepare_cocktail, cocktail)
    return CocktailStatus(status=PrepareResult.IN_PROGRESS)
