from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from src.api.internal.utils import map_bottles
from src.api.models import Bottle
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.machine.controller import MACHINE
from src.models import PrepareResult
from src.tabs import maker

router = APIRouter(tags=["bottles"], prefix="/bottles")


@router.get("")
async def get_bottles() -> list[Bottle]:
    DBC = DatabaseCommander()
    ingredients = DBC.get_ingredients_at_bottles()[: cfg.MAKER_NUMBER_BOTTLES]
    return [map_bottles(i) for i in ingredients]


@router.post("/refill")
async def refill_bottle(bottle_numbers: list[int], background_tasks: BackgroundTasks):
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        raise HTTPException(
            status_code=400, detail={"status": PrepareResult.IN_PROGRESS.value, "message": DH.cocktail_in_progress()}
        )
    DBC = DatabaseCommander()
    DBC.set_bottle_volumelevel_to_max(bottle_numbers)
    ingredients = []
    # check if any of those slots have a tube volume defined
    for num in bottle_numbers:
        ing = DBC.get_ingredient_at_bottle(num)
        pump_config = cfg.PUMP_CONFIG[num - 1]
        if pump_config.tube_volume > 0:
            ing.amount = pump_config.tube_volume
            ingredients.append(ing)
    # if there is at least one tube volume defined, flush the tubes
    if ingredients:
        background_tasks.add_task(MACHINE.make_cocktail, None, ingredients, "renew", False)
    return {"message": f"Bottle {bottle_numbers} refilled successfully!"}


@router.put("/{bottle_id}")
async def update_bottle(bottle_id: int, ingredient_id: int, amount: Optional[int] = None):
    DBC = DatabaseCommander()
    if amount is not None:
        DBC.set_ingredient_level_to_value(ingredient_id, amount)
    DBC.set_bottle_at_slot(ingredient_id, bottle_id)
    return {"message": f"Bottle {bottle_id} updated successfully to {amount} of ingredient {ingredient_id}!"}


@router.post("/{bottle_id}/calibrate", tags=["preparation"])
def calibrate_bottle(bottle_id: int, amount: int, background_tasks: BackgroundTasks):
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        return JSONResponse(
            status_code=400, content={"status": PrepareResult.IN_PROGRESS.value, "detail": DH.cocktail_in_progress()}
        )
    background_tasks.add_task(maker.calibrate, bottle_id, amount)
    return {"message": f"Bottle {bottle_id} calibration to {amount} started!"}
