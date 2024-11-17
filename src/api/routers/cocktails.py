# import asyncio
import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket

from src.api.internal.utils import calculate_cocktail_volume_and_concentration, map_cocktail
from src.api.models import Cocktail, CocktailInput, CocktailStatus, ErrorDetail, PrepareCocktailRequest
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.dialog_handler import DialogHandler
from src.models import Cocktail as DbCocktail
from src.models import PrepareResult
from src.tabs import maker
from src.utils import time_print

_dialog_handler = DialogHandler()
router = APIRouter(tags=["cocktails"], prefix="/cocktails")


@router.get("")
async def get_cocktails(only_possible: bool = True, max_hand_add: int = 3):
    DBC = DatabaseCommander()
    cocktails = DBC.get_possible_cocktails(max_hand_add) if only_possible else DBC.get_all_cocktails()
    return [map_cocktail(c) for c in cocktails]


@router.get("/{cocktail_id}")
async def get_cocktail(cocktail_id: int) -> Optional[Cocktail]:
    DBC = DatabaseCommander()
    cocktail = DBC.get_cocktail(cocktail_id)
    return map_cocktail(cocktail)


@router.post(
    "/prepare/{cocktail_id:int}",
    tags=["preparation"],
    responses={
        200: {"description": "Cocktail preparation started", "model": CocktailStatus},
        400: {"description": "Validation error", "model": ErrorDetail},
        404: {
            "description": "Cocktail not found",
            "content": {"application/json": {"example": {"detail": "Cocktail not found"}}},
        },
    },
)
async def prepare_cocktail(
    cocktail_id: int,
    request: PrepareCocktailRequest,
    background_tasks: BackgroundTasks,
) -> CocktailStatus:
    DBC = DatabaseCommander()
    factor = request.alcohol_factor if not request.is_virgin else 0
    cocktail = DBC.get_cocktail(cocktail_id)
    if cocktail is None:
        message = _dialog_handler.get_translation("element_not_found", element_name=f"Cocktail (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    cocktail.scale_cocktail(request.volume, factor)
    result, msg = maker.validate_cocktail(cocktail)
    if result != maker.PrepareResult.VALIDATION_OK:
        raise HTTPException(status_code=400, detail={"status": result.value, "detail": msg})
    background_tasks.add_task(maker.prepare_cocktail, cocktail)
    return CocktailStatus(status=PrepareResult.IN_PROGRESS)


@router.get("/prepare/status", tags=["preparation"])
async def get_cocktail_status() -> CocktailStatus:
    status = shared.cocktail_status
    return CocktailStatus(
        progress=status.progress, completed=status.completed, message=status.message, status=status.status
    )


@router.websocket("/ws/prepare/status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while shared.cocktail_status == "IN_PREPARATION":
        status = shared.cocktail_status
        await websocket.send_json(
            {
                "progress": status.progress,
                "completed": status.completed,
                "message": status.message,
                "status": status.status,
            }
        )
        await asyncio.sleep(0.2)
    await websocket.close()


@router.post("/prepare/stop", tags=["preparation"])
async def stop_cocktail():
    shared.cocktail_status.status = PrepareResult.CANCELED
    time_print("Canceling the cocktail!")
    return {"message": "Cocktail preparation stopped!"}


@router.post("")
async def create_cocktail(cocktail: CocktailInput) -> Optional[Cocktail]:
    DBC = DatabaseCommander()
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail = DBC.insert_new_recipe(
        cocktail.name, recipe_alcohol_level, recipe_volume, cocktail.enabled, cocktail.virgin_available, ingredient_data
    )
    return map_cocktail(db_cocktail)


@router.put("/{cocktail_id}")
async def update_cocktail(cocktail_id: int, cocktail: CocktailInput) -> Optional[Cocktail]:
    DBC = DatabaseCommander()
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
    DBC = DatabaseCommander()
    DBC.delete_recipe(cocktail_id)
    return {"message": f"Cocktail {cocktail_id} deleted successfully!"}
