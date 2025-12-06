import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect

from src.api.internal.nfc_payment import NFCPaymentHandler, get_nfc_payment_handler
from src.api.internal.utils import (
    calculate_cocktail_volume_and_concentration,
    map_cocktail,
    map_ingredient,
    not_on_demo,
)
from src.api.internal.validation import raise_on_validation_not_okay
from src.api.middleware import maker_protected
from src.api.models import (
    ApiMessage,
    ApiMessageWithData,
    Cocktail,
    CocktailInput,
    CocktailsAndIngredients,
    CocktailStatus,
    ErrorDetail,
    PaymentUserData,
    PrepareCocktailRequest,
)
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab, shared
from src.data_utils import select_optimal
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.image_utils import find_user_cocktail_image, process_image, save_image
from src.models import Cocktail as DbCocktail
from src.models import PrepareResult
from src.payment_utils import filter_cocktails_by_user
from src.programs.nfc_payment_service import User
from src.tabs import maker
from src.utils import time_print

_prefix = "/cocktails"
router = APIRouter(tags=["cocktails"], prefix=_prefix)
protected_maker_router = APIRouter(
    tags=["cocktails", "maker protected"],
    prefix=_prefix,
    dependencies=[
        Depends(maker_protected(Tab.MAKER)),
    ],
)
protected_recipes_router = APIRouter(
    tags=["cocktails", "maker protected"],
    prefix=_prefix,
    dependencies=[
        Depends(maker_protected(Tab.RECIPES)),
    ],
)


@router.get("", summary="Get all cocktails, limited to possible cocktails by default")
async def get_cocktails(
    only_possible: bool = True,
    max_hand_add: int = 3,
    scale: bool = True,
    payment_handler: Annotated[NFCPaymentHandler, Depends(get_nfc_payment_handler)] | None = None,
) -> list[Cocktail]:
    DBC = DatabaseCommander()
    cocktails = DBC.get_possible_cocktails(max_hand_add) if only_possible else DBC.get_all_cocktails()
    mapped_cocktails = [map_cocktail(c, scale) for c in cocktails if map_cocktail(c, scale) is not None]
    
    # Apply payment filtering if payment is active
    if cfg.PAYMENT_ACTIVE and payment_handler is not None:
        user = payment_handler.get_current_user()
        # Convert API Cocktail models back to DB Cocktail models for filtering
        db_cocktails = [DBC.get_cocktail(c.id) for c in mapped_cocktails]
        db_cocktails = [c for c in db_cocktails if c is not None]
        filtered_cocktails = filter_cocktails_by_user(user, db_cocktails)
        # Map filtered cocktails back to API models
        mapped_filtered = [map_cocktail(c, scale) for c in filtered_cocktails]
        return [c for c in mapped_filtered if c is not None]
    
    return mapped_cocktails


@router.get("/{cocktail_id:int}", summary="Get a cocktail by ID")
async def get_cocktail(cocktail_id: int) -> Cocktail:
    DBC = DatabaseCommander()
    cocktail = DBC.get_cocktail(cocktail_id)
    if cocktail is None:
        message = DH.get_translation("element_not_found", element_name=f"Cocktail (id={cocktail_id})")
        raise HTTPException(status_code=404, detail=message)
    return map_cocktail(cocktail)


@protected_maker_router.post(
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
    payment_handler: Annotated[NFCPaymentHandler, Depends(get_nfc_payment_handler)],
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
    if cfg.PAYMENT_ACTIVE:
        # Start payment flow - NFC scanning will happen first, then cocktail preparation
        background_tasks.add_task(payment_handler.start_payment_flow, cocktail)
        return CocktailStatus(status=PrepareResult.WAITING_FOR_NFC)
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


@protected_maker_router.post("/prepare/stop", tags=["preparation"], summary="Stop the current cocktail preparation")
async def stop_cocktail() -> ApiMessage:
    shared.cocktail_status.status = PrepareResult.CANCELED
    time_print("Canceling the cocktail!")
    return ApiMessage(message=DH.get_translation("preparation_cancelled"))


@protected_maker_router.post(
    "/prepare/payment/cancel",
    tags=["preparation", "payment"],
    summary="Cancel the current payment flow",
)
async def cancel_payment(
    payment_handler: Annotated[NFCPaymentHandler, Depends(get_nfc_payment_handler)],
) -> ApiMessage:
    booking = payment_handler.cancel_payment()
    shared.cocktail_status.status = PrepareResult.CANCELED
    shared.cocktail_status.message = booking.message
    time_print("Canceling the payment!")
    return ApiMessage(message=DH.get_translation("payment_canceled"))


@protected_recipes_router.post("", summary="Create a new cocktail", dependencies=[not_on_demo])
async def create_cocktail(cocktail: CocktailInput) -> ApiMessageWithData[Cocktail]:
    DBC = DatabaseCommander()
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail = DBC.insert_new_recipe(
        name=cocktail.name,
        alcohol_level=recipe_alcohol_level,
        volume=recipe_volume,
        price=cocktail.price_per_100_ml,
        enabled=cocktail.enabled,
        virgin=cocktail.virgin_available,
        ingredient_data=ingredient_data,
    )
    return ApiMessageWithData(
        message=DH.get_translation("recipe_added", recipe_name=db_cocktail.name),
        data=map_cocktail(db_cocktail, False),
    )


@protected_recipes_router.put("/{cocktail_id}", summary="Update a cocktail by ID", dependencies=[not_on_demo])
async def update_cocktail(cocktail_id: int, cocktail: CocktailInput) -> ApiMessageWithData[Cocktail]:
    DBC = DatabaseCommander()
    recipe_volume, recipe_alcohol_level = calculate_cocktail_volume_and_concentration(cocktail)
    ingredient_data = [(i.id, i.amount, i.recipe_order) for i in cocktail.ingredients]
    db_cocktail: DbCocktail = DBC.set_recipe(
        recipe_id=cocktail_id,
        name=cocktail.name,
        alcohol_level=recipe_alcohol_level,
        volume=recipe_volume,
        price=cocktail.price_per_100_ml,
        enabled=cocktail.enabled,
        virgin=cocktail.virgin_available,
        ingredient_data=ingredient_data,
    )
    return ApiMessageWithData(
        message=DH.get_translation("recipe_updated", old_name=cocktail_id, new_name=db_cocktail.name),
        data=map_cocktail(db_cocktail, False),
    )


@protected_recipes_router.delete("/{cocktail_id}", summary="Delete a cocktail by ID", dependencies=[not_on_demo])
async def delete_cocktail(cocktail_id: int) -> ApiMessage:
    DBC = DatabaseCommander()
    DBC.delete_recipe(cocktail_id)
    return ApiMessage(message=DH.get_translation("recipe_deleted", recipe_name=cocktail_id))


@protected_recipes_router.post(
    "/{cocktail_id}/image", summary="Upload an image for a cocktail", dependencies=[not_on_demo]
)
async def upload_cocktail_image(cocktail_id: int, file: Annotated[UploadFile, File(...)]) -> ApiMessage:
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


@protected_recipes_router.delete(
    "/{cocktail_id}/image", summary="Delete an image for a cocktail", dependencies=[not_on_demo]
)
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


@protected_recipes_router.post("/enable", summary="Enable all recipes")
async def enable_all_recipes() -> ApiMessage:
    DBC = DatabaseCommander()
    DBC.set_all_recipes_enabled()
    return ApiMessage(message=DH.get_translation("all_recipes_enabled"))


@router.get("/calculate", summary="Calculate optimal ingredient selection for given n and algorithm")
async def calculate_optimal_ingredient_selection(
    number_ingredients: Annotated[int, Query(ge=1)] = 10,
    algorithm: Literal["greedy", "local", "ilp"] = "ilp",
) -> CocktailsAndIngredients:
    ingredients, cocktails = select_optimal(number_ingredients, algorithm)
    return CocktailsAndIngredients(
        ingredients=[map_ingredient(i) for i in ingredients],
        cocktails=[map_cocktail(c, False) for c in cocktails],
    )


@router.websocket("/ws/payment/user")
async def websocket_payment_user(
    websocket: WebSocket,
) -> None:
    """WebSocket endpoint for user changes in payment system.
    
    Pushes user data and filtered cocktails when user changes.
    Only pushes data if payment is active.
    """
    await websocket.accept()
    
    if not cfg.PAYMENT_ACTIVE:
        await websocket.close()
        return
    
    payment_handler = get_nfc_payment_handler()
    DBC = DatabaseCommander()
    
    # Track previous user to detect changes
    prev_user_uid: str | None = None
    
    async def send_user_update(user: User | None, _nfc_id: str) -> None:
        """Send user and filtered cocktails to websocket."""
        nonlocal prev_user_uid
        
        # Only send if user actually changed
        current_uid = user.uid if user else None
        if current_uid == prev_user_uid:
            return
        
        prev_user_uid = current_uid
        
        try:
            # Get all possible cocktails
            cocktails = DBC.get_possible_cocktails(cfg.MAKER_MAX_HAND_INGREDIENTS)
            
            # Filter by user
            filtered_cocktails = filter_cocktails_by_user(user, cocktails)
            
            # Map to API models
            mapped_cocktails = [map_cocktail(c, True) for c in filtered_cocktails]
            mapped_cocktails = [c for c in mapped_cocktails if c is not None]
            
            # Prepare user data
            user_data = PaymentUserData(
                uid=user.uid if user else None,
                balance=user.balance if user else None,
                can_get_alcohol=user.can_get_alcohol if user else None,
            )
            
            # Send combined data
            await websocket.send_json({
                "user": user_data.model_dump(),
                "cocktails": [c.model_dump() for c in mapped_cocktails],
            })
        except Exception as e:
            time_print(f"Error sending user update via websocket: {e}")
    
    # Register callback with NFC service
    callback_name = f"websocket_{id(websocket)}"
    
    def nfc_callback(user: User | None, nfc_id: str) -> None:
        """Wrapper to schedule async send_user_update."""
        asyncio.create_task(send_user_update(user, nfc_id))
    
    payment_handler.nfc_service.add_callback(callback_name, nfc_callback)
    
    # Send initial state
    current_user = payment_handler.get_current_user()
    await send_user_update(current_user, current_user.uid if current_user else "")
    
    try:
        # Keep connection alive and listen for close
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        # Clean up callback when websocket closes
        payment_handler.nfc_service.remove_callback(callback_name)
        try:
            await websocket.close()
        except Exception:
            pass

