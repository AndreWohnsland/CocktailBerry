from fastapi import APIRouter

router = APIRouter(tags=["cocktails"], prefix="/cocktails")


@router.get("")
async def get_cocktails(only_possible: bool = True):
    return []


@router.get("/{cocktail_id}")
async def get_cocktail(cocktail_id: int):
    return {"cocktail_id": cocktail_id}


@router.post("/prepare/{cocktail_id}")
async def prepare_cocktail(cocktail_id: int, volume: int, alcohol_factor: float, is_virgin: bool = False):
    factor = alcohol_factor if not is_virgin else 0
    return {"message": f"Cocktail {cocktail_id} of volume {volume} ({factor}%) prepared successfully!"}


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
