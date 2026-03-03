from __future__ import annotations

import asyncio
import contextlib

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.api.api_config import Tags
from src.api.internal.utils import not_on_demo
from src.api.middleware import master_protected_dependency
from src.api.models import ApiMessage, CurrentWaiterState, WaiterCreate, WaiterLogEntry, WaiterResponse, WaiterUpdate
from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.logger_handler import LoggerHandler
from src.service.waiter_service import WaiterService

_logger = LoggerHandler("waiter_router")


router = APIRouter(prefix="/waiters", tags=[Tags.WAITERS])
protected_router = APIRouter(
    prefix="/waiters",
    tags=[Tags.WAITERS, Tags.MASTER_PROTECTED],
    dependencies=[Depends(master_protected_dependency)],
)


@router.get("/current", summary="Get the current waiter state")
async def get_current_waiter() -> WaiterResponse | None:
    """Get the current registered waiter, or null if none is logged in."""
    return shared.current_waiter  # pyright: ignore[reportAttributeAccessIssue]


@router.post("/logout", summary="Log out the current waiter")
async def logout_current_waiter() -> ApiMessage:
    """Log out the current waiter by clearing shared state and notifying clients."""
    WaiterService().logout_waiter()
    _notify_waiter_callbacks()
    return ApiMessage(message="Service Personnel logged out")


@protected_router.get("", summary="List all registered waiters")
async def get_waiters() -> list[WaiterResponse]:
    """Get all registered waiters."""
    DBC = DatabaseCommander()
    waiters = DBC.get_all_waiters()
    return [WaiterResponse.from_db(w) for w in waiters]


@protected_router.post("", summary="Register a new waiter", dependencies=[not_on_demo])
async def create_waiter(data: WaiterCreate) -> WaiterResponse:
    """Register a new waiter with NFC ID and name."""
    DBC = DatabaseCommander()
    permissions = data.permissions.model_dump() if data.permissions else None
    waiter = DBC.create_waiter(data.nfc_id, data.name, permissions=permissions)
    response = WaiterResponse.from_db(waiter)
    # If the newly registered NFC ID is the currently scanned one, update shared state
    if shared.current_waiter_nfc_id == data.nfc_id:
        shared.current_waiter = response
        _notify_waiter_callbacks()
    return response


@protected_router.put("/{nfc_id}", summary="Update a waiter", dependencies=[not_on_demo])
async def update_waiter(nfc_id: str, data: WaiterUpdate) -> WaiterResponse:
    """Update a waiter's name and/or permissions."""
    DBC = DatabaseCommander()
    permissions = data.permissions.model_dump() if data.permissions else None
    waiter = DBC.update_waiter(nfc_id, name=data.name, permissions=permissions)
    response = WaiterResponse.from_db(waiter)
    # Update shared state if this is the current waiter
    if shared.current_waiter_nfc_id == nfc_id:
        shared.current_waiter = response
        _notify_waiter_callbacks()
    return response


@protected_router.delete("/{nfc_id}", summary="Delete a waiter", dependencies=[not_on_demo])
async def delete_waiter(nfc_id: str) -> ApiMessage:
    """Delete a waiter by NFC ID. Unsets current waiter if it matches."""
    DBC = DatabaseCommander()
    DBC.delete_waiter(nfc_id)
    # Unset current waiter if they were just deleted
    if shared.current_waiter_nfc_id == nfc_id:
        shared.current_waiter = None
        _notify_waiter_callbacks()
    return ApiMessage(message="Service Personnel deleted successfully")


@protected_router.get("/logs", summary="Get waiter cocktail logs")
async def get_waiter_logs() -> list[WaiterLogEntry]:
    """Get all waiter cocktail logs with waiter and recipe names."""
    DBC = DatabaseCommander()
    logs = DBC.get_waiter_logs()
    return [
        WaiterLogEntry(
            id=log.id,
            timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            waiter_name=log.waiter.name if log.waiter else "Deleted User",
            recipe_name=log.recipe.name if log.recipe else "Deleted Recipe",
            volume=log.volume,
            is_virgin=log.is_virgin,
        )
        for log in logs
    ]


@router.websocket("/ws/current")
async def websocket_waiter_current(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time waiter state updates.

    Pushes current waiter state when the waiter changes (NFC scan, logout, etc.).
    """
    await websocket.accept()

    if not cfg.waiter_mode_active:
        await websocket.close()
        return

    loop = asyncio.get_running_loop()

    async def send_waiter_state() -> None:
        """Send current waiter state to websocket."""
        try:
            state = CurrentWaiterState(nfc_id=shared.current_waiter_nfc_id, waiter=shared.current_waiter)
            await websocket.send_json(state.model_dump())
        except Exception as e:
            _logger.debug(f"Error sending waiter update via websocket: {e}")

    callback_name = f"websocket_{id(websocket)}"

    def waiter_callback() -> None:
        """Schedule async send from another thread."""
        asyncio.run_coroutine_threadsafe(send_waiter_state(), loop)

    waiter_service = WaiterService()
    waiter_service.add_callback(callback_name, waiter_callback)

    # Send initial state
    await send_waiter_state()

    try:
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        waiter_service.remove_callback(callback_name)
        with contextlib.suppress(Exception):
            await websocket.close()


def _notify_waiter_callbacks() -> None:
    """Notify waiter service callbacks of state changes (e.g. after CRUD operations)."""
    if cfg.waiter_mode_active:
        waiter_service = WaiterService()
        waiter_service._run_callbacks()
