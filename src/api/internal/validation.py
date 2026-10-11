from __future__ import annotations

from fastapi import HTTPException

from src.dialog_handler import DIALOG_HANDLER as DH
from src.machine.controller import claim_machine, machine_is_busy
from src.models import Cocktail, PrepareResult
from src.service import preparation


class ValidationError(HTTPException):
    def __init__(self, status: str, detail: str, bottle: int | None = None, status_code: int = 400) -> None:
        self.status = status
        self.detail_msg = detail
        self.bottle = bottle
        super().__init__(status_code=status_code, detail=detail)


def raise_when_cocktail_is_in_progress() -> None:
    """Raise an HTTPException if a pump run or payment wait owns the machine."""
    if machine_is_busy():
        raise ValidationError(
            status=PrepareResult.IN_PROGRESS.value,
            detail=DH.cocktail_in_progress(),
            bottle=None,
        )


def claim_machine_or_raise(status: PrepareResult) -> None:
    """Raise an HTTPException if another preparation claimed the machine first."""
    if not claim_machine(status):
        raise ValidationError(
            status=PrepareResult.IN_PROGRESS.value,
            detail=DH.cocktail_in_progress(),
        )


def raise_on_validation_not_okay(cocktail: Cocktail) -> None:
    result, msg, ingredient = preparation.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        raise ValidationError(
            status=result.value,
            detail=msg,
            bottle=ingredient.bottle if ingredient is not None else None,
        )
