from fastapi import APIRouter

from src.api.api_config import Tags
from src.models import BlackList
from src.programs.blacklist import BLACKLIST

router = APIRouter(tags=[Tags.OPTIONS], prefix="/blacklist")


@router.get(
    "",
    summary="Get the producer-defined blacklist of configs and option tiles",
)
async def get_blacklist() -> BlackList:
    """Return the active blacklist.

    The blacklist is read-only at runtime and exposed publicly so the frontend
    can hide tiles before any login. Enforcement is UI-only — protected
    endpoints continue to work with the master password.
    """
    return BLACKLIST.blacklist
