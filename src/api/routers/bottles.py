from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.api.internal.utils import map_bottles
from src.api.internal.validation import raise_when_cocktail_is_in_progress
from src.api.middleware import maker_protected
from src.api.models import ApiMessage, Bottle
from src.config.config_manager import CONFIG as cfg
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.machine.controller import MachineController
from src.tabs import maker

router = APIRouter(tags=["bottles"], prefix="/bottles")
protected_router = APIRouter(
    tags=["bottles", "maker protected"],
    prefix="/bottles",
    dependencies=[
        Depends(maker_protected(2)),
    ],
)


@router.get("", summary="Get all bottles with their ingredients.")
async def get_bottles() -> list[Bottle]:
    DBC = DatabaseCommander()
    ingredients = DBC.get_ingredients_at_bottles()[: cfg.MAKER_NUMBER_BOTTLES]
    return [map_bottles(i) for i in ingredients]


@protected_router.post("/refill", summary="Refill all given bottles to maximum.")
async def refill_bottle(bottle_numbers: list[int], background_tasks: BackgroundTasks) -> ApiMessage:
    raise_when_cocktail_is_in_progress()
    if any(num < 1 or num > cfg.MAKER_NUMBER_BOTTLES for num in bottle_numbers):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bottle number, valid_range 1-{cfg.MAKER_NUMBER_BOTTLES}",
        )
    DBC = DatabaseCommander()
    DBC.set_bottle_volumelevel_to_max(bottle_numbers)
    ingredients = []
    # check if any of those slots have a tube volume defined
    for num in bottle_numbers:
        ing = DBC.get_ingredient_at_bottle(num)
        pump_config = cfg.PUMP_CONFIG[num - 1]
        if ing is None:
            continue
        if pump_config.tube_volume > 0:
            ing.amount = pump_config.tube_volume
            ingredients.append(ing)
    # if there is at least one tube volume defined, flush the tubes
    if ingredients:
        mc = MachineController()
        background_tasks.add_task(mc.make_cocktail, None, ingredients, "renew", False)
    return ApiMessage(message=f"{DH.get_translation('bottles_renewed')} {bottle_numbers}")


@protected_router.put("/{bottle_id}", summary="Update bottle to ingredient and fill level.")
async def update_bottle(bottle_id: int, ingredient_id: int, amount: Optional[int] = None) -> ApiMessage:
    DBC = DatabaseCommander()
    ingredients = DBC.get_ingredients_at_bottles()[: cfg.MAKER_NUMBER_BOTTLES]
    # cannot assign the same ingredient to multiple bottles
    # Skip if remove bottle
    if ingredient_id != 0:
        already_at_slot = next((i.bottle for i in ingredients if i.id == ingredient_id and i.bottle != bottle_id), None)
        if already_at_slot is not None:
            raise HTTPException(
                status_code=400,
                detail=f"Ingredient already at slot {already_at_slot}",
            )
    if amount is not None:
        DBC.set_ingredient_level_to_value(ingredient_id, amount)
    DBC.set_bottle_at_slot(ingredient_id, bottle_id)
    return ApiMessage(
        message=DH.get_translation("bottle_updated", bottle_id=bottle_id, amount=amount, ingredient_id=ingredient_id)
    )


@protected_router.post("/{bottle_id}/calibrate", tags=["preparation"], summary="Calibrate bottle with given amount.")
def calibrate_bottle(bottle_id: int, amount: int, background_tasks: BackgroundTasks) -> ApiMessage:
    raise_when_cocktail_is_in_progress()
    background_tasks.add_task(maker.calibrate, bottle_id, amount)
    return ApiMessage(message=DH.get_translation("bottle_calibration_started", bottle_id=bottle_id, amount=amount))
