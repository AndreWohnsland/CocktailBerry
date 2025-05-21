from fastapi import HTTPException

from src.config.config_manager import shared
from src.dialog_handler import DIALOG_HANDLER as DH
from src.models import Cocktail, PrepareResult
from src.tabs import maker


class ValidationError(HTTPException):
    def __init__(self, status: str, detail: str, bottle: int | None = None, status_code: int = 400) -> None:
        self.status = status
        self.detail_msg = detail
        self.bottle = bottle
        super().__init__(status_code=status_code, detail=detail)


def raise_when_cocktail_is_in_progress() -> None:
    """Raise an HTTPException if a cocktail is in progress."""
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        raise ValidationError(
            status=PrepareResult.IN_PROGRESS.value,
            detail=DH.cocktail_in_progress(),
            bottle=None,
        )


def raise_on_validation_not_okay(cocktail: Cocktail) -> None:
    result, msg, ingredient = maker.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        raise ValidationError(
            status=result.value,
            detail=msg,
            bottle=ingredient.bottle if ingredient is not None else None,
        )
