import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, WebSocket
from fastapi.responses import JSONResponse

from src.api.internal.utils import calculate_cocktail_volume_and_concentration, map_cocktail
from src.api.middleware import maker_protected
from src.api.models import Cocktail, CocktailInput, CocktailStatus, ErrorDetail, PrepareCocktailRequest
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


@router.get("")
async def get_cocktails(only_possible: bool = True, max_hand_add: int = 3, scale: bool = True) -> list[Cocktail]:
    DBC = DatabaseCommander()
    cocktails = DBC.get_possible_cocktails(max_hand_add) if only_possible else DBC.get_all_cocktails()
    mapped_cocktails = [map_cocktail(c, scale) for c in cocktails]
    return [c for c in mapped_cocktails if c is not None]


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
):
    DBC = DatabaseCommander()
    factor = request.alcohol_factor if not request.is_virgin else 0
    cocktail = DBC.get_cocktail(cocktail_id)
    if cocktail is None:
        message = DH.get_translation("element_not_found", element_name=f"Cocktail (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    cocktail.scale_cocktail(request.volume, factor)
    result, msg, ingredient = maker.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        # we need also provide the frontend with the ingredient id that caused the error
        bottle = ingredient.bottle if ingredient is not None else None
        return JSONResponse(status_code=400, content={"status": result.value, "detail": msg, "bottle": bottle})
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
    return {"message": DH.get_translation("preparation_cancelled")}


@protected_router.post("")
async def create_cocktail(cocktail: CocktailInput) -> Optional[Cocktail]:
    DBC = DatabaseCommander()
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail = DBC.insert_new_recipe(
        cocktail.name, recipe_alcohol_level, recipe_volume, cocktail.enabled, cocktail.virgin_available, ingredient_data
    )
    return {
        "message": DH.get_translation("recipe_added", recipe_name=db_cocktail.name),
        "cocktail": map_cocktail(db_cocktail, False),
    }


@protected_router.put("/{cocktail_id}")
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
    return {
        "message": DH.get_translation("recipe_updated", old_name=cocktail_id, new_name=db_cocktail.name),
        "cocktail": map_cocktail(db_cocktail, False),
    }


@protected_router.delete("/{cocktail_id}")
async def delete_cocktail(cocktail_id: int):
    DBC = DatabaseCommander()
    DBC.delete_recipe(cocktail_id)
    return {"message": DH.get_translation("recipe_deleted", recipe_name=cocktail_id)}


@protected_router.post("/{cocktail_id}/image")
async def upload_cocktail_image(cocktail_id: int, file: UploadFile = File(...)):
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
    return {"message": DH.get_translation("image_uploaded")}


@protected_router.delete("/{cocktail_id}/image")
async def delete_cocktail_image(cocktail_id: int):
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
    return {"message": DH.get_translation("image_deleted")}


@protected_router.post("/enable")
async def enable_all_recipes():
    DBC = DatabaseCommander()
    DBC.set_all_recipes_enabled()
    return {"message": DH.get_translation("all_recipes_enabled")}
