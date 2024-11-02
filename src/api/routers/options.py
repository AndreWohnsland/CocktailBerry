from fastapi import APIRouter

router = APIRouter(tags=["options"], prefix="/options")


@router.get("")
async def get_options():
    return []


@router.post("/update")
async def update_options(options: dict):
    return {"message": f"Options {options} updated successfully!"}
