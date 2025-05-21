import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, WebSocket

from src.api.internal.utils import calculate_cocktail_volume_and_concentration, map_cocktail, not_on_demo
from src.api.internal.validation import raise_on_validation_not_okay
from src.api.middleware import maker_protected
from src.api.models import (
    ApiMessage,
    ApiMessageWithData,
    Cocktail,
    CocktailInput,
    CocktailStatus,
    ErrorDetail,
    PrepareCocktailRequest,
)
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.image_utils import find_user_cocktail_image, process_image, save_image
from src.models import Cocktail as DbCocktail
from src.models import PrepareResult
from src.tabs import maker
from src.utils import time_print

router = APIRouter(tags=["cocktails"], prefix="/cocktails")
protected_router = APIRouter(
    tags=["cocktails", "maker protected"],
    prefix="/cocktails",
    dependencies=[
        Depends(maker_protected(1)),
    ],
)


@router.get("", summary="Get all cocktails, limited to possible cocktails by default")
async def get_cocktails(only_possible: bool = True, max_hand_add: int = 3, scale: bool = True) -> list[Cocktail]:
    DBC = DatabaseCommander()
    cocktails = DBC.get_possible_cocktails(max_hand_add) if only_possible else DBC.get_all_cocktails()
    mapped_cocktails = [map_cocktail(c, scale) for c in cocktails]
    return [c for c in mapped_cocktails if c is not None]


@router.get("/{cocktail_id}", summary="Get a cocktail by ID")
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
    summary="Prepare a cocktail by ID and defined properties",
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
        message = DH.get_translation("element_not_found", element_name=f"Cocktail (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    cocktail.scale_cocktail(request.volume, factor)
    # need to check if the cocktail is possible
    # this can happen if there is no ui guidance, e.g. only a direct post of an id
    # the cocktail might only be possible in the virgin version, but the user requested a non-virgin version
    hand_ids = DBC.get_available_ids()
    if not cocktail.is_possible(hand_ids, cfg.MAKER_MAX_HAND_INGREDIENTS) or (
        cocktail.only_virgin and not cocktail.is_virgin
    ):
        raise HTTPException(status_code=400, detail=DH.get_translation("cocktail_not_possible"))
    raise_on_validation_not_okay(cocktail)
    # handle team data
    shared.team_member_name = None
    shared.selected_team = "No Team"
    if request.selected_team is not None:
        shared.selected_team = request.selected_team
        shared.team_member_name = request.team_member_name
    background_tasks.add_task(maker.prepare_cocktail, cocktail)
    return CocktailStatus(status=PrepareResult.IN_PROGRESS)


@router.get("/prepare/status", tags=["preparation"], summary="Get the current cocktail preparation status")
async def get_cocktail_status() -> CocktailStatus:
    status = shared.cocktail_status
    return CocktailStatus(
        progress=status.progress, completed=status.completed, message=status.message, status=status.status
    )


@router.websocket("/ws/prepare/status")
async def websocket_endpoint(websocket: WebSocket) -> None:
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


@router.post("/prepare/stop", tags=["preparation"], summary="Stop the current cocktail preparation")
async def stop_cocktail() -> ApiMessage:
    shared.cocktail_status.status = PrepareResult.CANCELED
    time_print("Canceling the cocktail!")
    return ApiMessage(message=DH.get_translation("preparation_cancelled"))


@protected_router.post("", summary="Create a new cocktail", dependencies=[not_on_demo])
async def create_cocktail(cocktail: CocktailInput) -> ApiMessageWithData[Cocktail]:
    DBC = DatabaseCommander()
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail = DBC.insert_new_recipe(
        cocktail.name, recipe_alcohol_level, recipe_volume, cocktail.enabled, cocktail.virgin_available, ingredient_data
    )
    return ApiMessageWithData(
        message=DH.get_translation("recipe_added", recipe_name=db_cocktail.name),
        data=map_cocktail(db_cocktail, False),
    )


@protected_router.put("/{cocktail_id}", summary="Update a cocktail by ID", dependencies=[not_on_demo])
async def update_cocktail(cocktail_id: int, cocktail: CocktailInput) -> ApiMessageWithData[Cocktail]:
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
    return ApiMessageWithData(
        message=DH.get_translation("recipe_updated", old_name=cocktail_id, new_name=db_cocktail.name),
        data=map_cocktail(db_cocktail, False),
    )


@protected_router.delete("/{cocktail_id}", summary="Delete a cocktail by ID", dependencies=[not_on_demo])
async def delete_cocktail(cocktail_id: int) -> ApiMessage:
    DBC = DatabaseCommander()
    DBC.delete_recipe(cocktail_id)
    return ApiMessage(message=DH.get_translation("recipe_deleted", recipe_name=cocktail_id))


@protected_router.post("/{cocktail_id}/image", summary="Upload an image for a cocktail", dependencies=[not_on_demo])
async def upload_cocktail_image(cocktail_id: int, file: UploadFile = File(...)) -> ApiMessage:
    DBC = DatabaseCommander()
    cocktail = DBC.get_cocktail(cocktail_id)
    if cocktail is None:
        message = DH.get_translation("element_not_found", element_name=f"Cocktail (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    try:
        contents = await file.read()
        image = process_image(contents)
        if image is None:
            raise HTTPException(status_code=400, detail="Image processing failed.")
        save_image(image, cocktail_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to upload image: {e!s}")
    return ApiMessage(message=DH.get_translation("image_uploaded"))


@protected_router.delete("/{cocktail_id}/image", summary="Delete an image for a cocktail", dependencies=[not_on_demo])
async def delete_cocktail_image(cocktail_id: int) -> ApiMessage:
    DBC = DatabaseCommander()
    cocktail = DBC.get_cocktail(cocktail_id)
    if cocktail is None:
        message = DH.get_translation("element_not_found", element_name=f"Cocktail (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    user_image_path = find_user_cocktail_image(cocktail)
    if user_image_path is None or not user_image_path.exists():
        message = DH.get_translation("element_not_found", element_name=f"Cocktail Image (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    try:
        user_image_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete image: {e!s}")
    return ApiMessage(message=DH.get_translation("image_deleted"))


@protected_router.post("/enable", summary="Enable all recipes")
async def enable_all_recipes() -> ApiMessage:
    DBC = DatabaseCommander()
    DBC.set_all_recipes_enabled()
    return ApiMessage(message=DH.get_translation("all_recipes_enabled"))
