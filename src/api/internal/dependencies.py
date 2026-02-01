"""FastAPI dependency injection classes and functions."""

from typing import Annotated

from fastapi import Depends, HTTPException

from src.config.config_manager import CONFIG as cfg
from src.service.sumup_payment_service import SumupPaymentService


def get_sumup_service() -> SumupPaymentService:
    """Dependency to get or create the SumUp service instance.

    Raises:
        HTTPException: If SumUp API key or merchant code is not configured.

    Returns:
        SumupPaymentService: The configured SumUp payment service.

    """
    if not cfg.PAYMENT_SUMUP_API_KEY or not cfg.PAYMENT_SUMUP_MERCHANT_CODE:
        raise HTTPException(
            status_code=400,
            detail="SumUp API key and merchant code must be configured first.",
        )
    return SumupPaymentService(
        api_key=cfg.PAYMENT_SUMUP_API_KEY,
        merchant_code=cfg.PAYMENT_SUMUP_MERCHANT_CODE,
    )


# Type alias for dependency injection
SumupServiceDep = Annotated[SumupPaymentService, Depends(get_sumup_service)]
