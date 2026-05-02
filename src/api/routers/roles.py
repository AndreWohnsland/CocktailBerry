from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.api_config import Tags
from src.api.internal.utils import not_on_demo
from src.api.middleware import master_protected_dependency
from src.api.models import ApiMessage, RoleCreate, RoleResponse, RoleUpdate
from src.database_commander import DatabaseCommander, ElementNotFoundError, RoleInUseError

router = APIRouter(
    prefix="/roles",
    tags=[Tags.WAITERS, Tags.MASTER_PROTECTED],
    dependencies=[Depends(master_protected_dependency)],
)


@router.get("", summary="List all roles")
async def get_roles() -> list[RoleResponse]:
    """Get all defined roles."""
    DBC = DatabaseCommander()
    return [RoleResponse.from_db(r) for r in DBC.get_all_roles()]


@router.post("", summary="Create a new role", dependencies=[not_on_demo])
async def create_role(data: RoleCreate) -> RoleResponse:
    """Create a new role with tab and tile permissions."""
    DBC = DatabaseCommander()
    role = DBC.create_role(
        data.name,
        permissions=data.permissions.model_dump(),
        tile_permissions=data.tile_permissions.model_dump(),
    )
    return RoleResponse.from_db(role)


@router.put("/{role_id}", summary="Update a role", dependencies=[not_on_demo])
async def update_role(role_id: int, data: RoleUpdate) -> RoleResponse:
    """Update a role's name, tab permissions, and/or tile permissions."""
    DBC = DatabaseCommander()
    role = DBC.update_role(
        role_id,
        name=data.name,
        permissions=data.permissions.model_dump() if data.permissions else None,
        tile_permissions=data.tile_permissions.model_dump() if data.tile_permissions else None,
    )
    return RoleResponse.from_db(role)


@router.delete("/{role_id}", summary="Delete a role", dependencies=[not_on_demo])
async def delete_role(role_id: int) -> ApiMessage:
    """Delete a role. Fails with 409 if any waiter still references it."""
    DBC = DatabaseCommander()
    try:
        DBC.delete_role(role_id)
    except RoleInUseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ElementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiMessage(message="Role deleted successfully")
