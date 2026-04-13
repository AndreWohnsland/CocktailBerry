from fastapi import APIRouter, Depends, HTTPException

from src.api.api_config import Tags
from src.api.middleware import master_protected_dependency
from src.api.models import ApiMessageWithData
from src.dialog_handler import DIALOG_HANDLER as DH
from src.machine.controller import MachineController

router = APIRouter(tags=[Tags.SCALE], prefix="/scale")
protected_router = APIRouter(
    tags=[Tags.SCALE, Tags.MASTER_PROTECTED],
    prefix="/scale",
    dependencies=[Depends(master_protected_dependency)],
)


def _require_scale() -> MachineController:
    """Get the MachineController and verify scale is available."""
    mc = MachineController()
    if not mc.has_scale:
        raise HTTPException(status_code=400, detail=DH.get_translation("no_scale_available"))
    return mc


@router.get("/status", summary="Check if scale is available.")
async def get_scale_status() -> ApiMessageWithData[bool]:
    mc = MachineController()
    return ApiMessageWithData(message="Scale status", data=mc.has_scale)


@protected_router.post("/tare", summary="Tare (zero) the scale.")
async def tare_scale() -> ApiMessageWithData[float]:
    mc = _require_scale()
    offset = mc.scale_tare()
    return ApiMessageWithData(message=DH.get_translation("scale_tared"), data=offset)


@protected_router.post("/read", summary="Read current weight in grams.")
async def read_scale() -> ApiMessageWithData[float]:
    mc = _require_scale()
    weight = mc.scale_read_grams()
    return ApiMessageWithData(message="Scale reading", data=round(weight, 1))


@protected_router.post("/calibrate", summary="Calibrate the scale using a known weight.")
async def calibrate_scale(known_weight_grams: float, zero_raw_offset: int) -> ApiMessageWithData[float]:
    mc = _require_scale()
    if known_weight_grams <= 0:
        raise HTTPException(status_code=400, detail=DH.get_translation("scale_known_weight_positive"))
    try:
        factor = mc.scale_calibrate(known_weight_grams, zero_raw_offset=zero_raw_offset)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiMessageWithData(message=DH.get_translation("scale_calibrated", factor=f"{factor:.4f}"), data=factor)
