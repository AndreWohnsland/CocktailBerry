import asyncio
from typing import Optional

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from src.api.models import Cocktail, map_cocktail
from src.database_commander import DB_COMMANDER as DBC

router = APIRouter(tags=["cocktails"], prefix="/cocktails")


@router.get("")
async def get_cocktails(only_possible: bool = True):
    cocktails = DBC.get_possible_cocktails() if only_possible else DBC.get_all_cocktails()
    return [map_cocktail(c) for c in cocktails]


@router.get("/{cocktail_id}")
async def get_cocktail(cocktail_id: int) -> Optional[Cocktail]:
    cocktail = DBC.get_cocktail(cocktail_id)
    return map_cocktail(cocktail)


@router.get("/prepare/{cocktail_id}")
async def prepare_cocktail(cocktail_id: int, volume: int, alcohol_factor: float, is_virgin: bool = False):
    factor = alcohol_factor if not is_virgin else 0
    cocktail = DBC.get_cocktail(cocktail_id)

    # TODO: implement cocktail preparation with sockets
    # return {"message": f"Cocktail {cocktail} of volume {volume} ({factor}%) prepared successfully!"}
    async def event_generator():
        i = 0
        while i < 10:
            i += 1
            yield f"Cocktail {cocktail} of volume {volume} ({factor}%) {i}/10"
            await asyncio.sleep(0.3)
        yield "done"

    return EventSourceResponse(event_generator(), ping=100)


# TODO: Cocktail CRUD management


@router.post("")
async def create_cocktail():
    return {"message": "Cocktail created successfully!"}


@router.put("/{cocktail_id}")
async def update_cocktail(cocktail_id: int):
    return {"message": f"Cocktail {cocktail_id} updated successfully!"}


@router.delete("/{cocktail_id}")
async def delete_cocktail(cocktail_id: int):
    return {"message": f"Cocktail {cocktail_id} deleted successfully!"}
