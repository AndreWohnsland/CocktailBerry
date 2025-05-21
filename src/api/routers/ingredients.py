from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.api.internal.utils import map_ingredient, not_on_demo
from src.api.internal.validation import raise_on_validation_not_okay
from src.api.middleware import maker_protected
from src.api.models import ApiMessage, ApiMessageWithData, ErrorDetail, Ingredient, IngredientInput
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.models import Cocktail, CocktailStatus, PrepareResult
from src.tabs import maker

router = APIRouter(tags=["ingredients"], prefix="/ingredients")
protected_router = APIRouter(
    tags=["ingredients", "maker protected"],
    prefix="/ingredients",
    dependencies=[
        Depends(maker_protected(0)),
    ],
)


@router.get("", summary="Get all ingredients, filtered by machine and hand")
async def get_ingredients(machine: bool = True, hand: bool = True) -> list[Ingredient]:
    DBC = DatabaseCommander()
    ingredients = DBC.get_all_ingredients(get_machine=machine, get_hand=hand)
    return [map_ingredient(i) for i in ingredients]


# TODO: Check if a 404 is better than a None returned here
@router.get("/{ingredient_id:int}", summary="Get ingredient by ID")
async def get_ingredient(ingredient_id: int) -> Ingredient | None:
    DBC = DatabaseCommander()
    ingredient = DBC.get_ingredient(ingredient_id)
    return map_ingredient(ingredient)


@protected_router.post("", summary="Add new ingredient", dependencies=[not_on_demo])
async def add_ingredient(ingredient: IngredientInput) -> ApiMessageWithData[Ingredient]:
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
    if db_ingredient is None:
        raise HTTPException(status_code=400, detail="Critical error: ingredient not found after creation")
    return ApiMessageWithData(
        message=DH.get_translation("ingredient_added", ingredient_name=ingredient.name),
        data=map_ingredient(db_ingredient),
    )


@protected_router.put("/{ingredient_id:int}", summary="Update ingredient by ID", dependencies=[not_on_demo])
async def update_ingredient(ingredient_id: int, ingredient: IngredientInput) -> ApiMessageWithData[Ingredient]:
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
    db_ingredient = DBC.get_ingredient(ingredient_id)
    if db_ingredient is None:
        raise HTTPException(status_code=400, detail="Critical error: ingredient not found after update")
    return ApiMessageWithData(
        message=DH.get_translation(
            "ingredient_changed", selected_ingredient=ingredient_id, ingredient_name=ingredient.name
        ),
        data=map_ingredient(db_ingredient),
    )


@protected_router.delete("/{ingredient_id:int}", summary="Delete ingredient by ID", dependencies=[not_on_demo])
async def delete_ingredients(ingredient_id: int) -> ApiMessage:
    DBC = DatabaseCommander()
    DBC.delete_ingredient(ingredient_id)
    return ApiMessage(message=DH.get_translation("ingredient_deleted", ingredient_name=ingredient_id))


@router.get("/available", summary="Get available ingredients IDs")
async def get_available_ingredients() -> list[int]:
    DBC = DatabaseCommander()
    return DBC.get_available_ids()


@protected_router.post("/available")
async def post_available_ingredients(available: list[int]) -> ApiMessage:
    DBC = DatabaseCommander()
    DBC.delete_existing_handadd_ingredient()
    DBC.insert_multiple_existing_handadd_ingredients(available)
    return ApiMessage(message=DH.get_translation("available_ingredient_updated"))


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
    summary="Prepare given amount of ingredient by ID",
)
async def prepare_ingredient(ingredient_id: int, amount: int, background_tasks: BackgroundTasks) -> CocktailStatus:
    DBC = DatabaseCommander()
    ingredient = DBC.get_ingredient(ingredient_id)
    if ingredient is None:
        message = DH.get_translation("element_not_found", element_name=f"Ingredient (id={ingredient_id})")
        raise HTTPException(status_code=404, detail=message)
    if ingredient.hand:
        raise HTTPException(
            status_code=400,
            detail=DH.get_translation("hand_ingredient_cannot_prepared"),
        )
    if ingredient.bottle is None:
        raise HTTPException(
            status_code=400,
            detail=DH.get_translation("ingredient_not_connected"),
        )
    ingredient.amount = amount
    cocktail = Cocktail(0, ingredient.name, 0, amount, True, True, [ingredient])
    raise_on_validation_not_okay(cocktail)
    background_tasks.add_task(maker.prepare_cocktail, cocktail)
    return CocktailStatus(status=PrepareResult.IN_PROGRESS)
