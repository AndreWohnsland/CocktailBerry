from typing import Optional

from fastapi import APIRouter

router = APIRouter(tags=["bottles"], prefix="/bottles")


@router.get("")
async def get_bottles():
    return []


@router.post("/refill/{bottle_id}")
async def refill_bottle(bottle_id: int):
    return {"message": f"Bottle {bottle_id} refilled successfully!"}


@router.put("/{bottle_id}")
async def update_bottle(bottle_id: int, ingredient_id: Optional[int] = None, amount: Optional[int] = None):
    return {"message": f"Bottle {bottle_id} updated successfully!"}
