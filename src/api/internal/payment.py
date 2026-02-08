"""Payment handler abstraction for V2 API.

This module provides a unified interface for different payment handlers
(NFC, SumUp, or disabled) through a Protocol class and a factory dependency.
"""

from functools import lru_cache
from typing import Protocol

from src.api.internal.nfc_payment import get_nfc_payment_handler
from src.api.internal.sumup_payment import get_sumup_payment_handler
from src.config.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.models import Cocktail
from src.service.booking import CocktailBooking

_logger = LoggerHandler("payment_handler")


class PaymentHandler(Protocol):
    """Protocol defining the interface for payment handlers."""

    async def start_payment_flow(self, cocktail: Cocktail) -> None:
        """Start the payment flow for a cocktail.

        This method should handle the complete payment process including
        status updates and cocktail preparation on success.
        """
        ...

    def cancel_payment(self) -> CocktailBooking:
        """Cancel the ongoing payment flow.

        Returns:
            CocktailBooking with the cancellation result.

        """
        ...


class DisabledPaymentHandler:
    """Dummy payment handler when payment is disabled.

    This handler logs info messages and returns inactive booking results.
    """

    async def start_payment_flow(self, cocktail: Cocktail) -> None:
        """Log that payment is disabled - this should not normally be called."""
        _logger.info(f"Payment disabled: skipping payment flow for cocktail '{cocktail.name}'")

    def cancel_payment(self) -> CocktailBooking:
        """Return inactive booking since payment is disabled."""
        _logger.info("Payment disabled: cancel_payment called but no active payment")
        return CocktailBooking.inactive()


@lru_cache
def _get_disabled_payment_handler() -> DisabledPaymentHandler:
    """Get or create the disabled payment handler singleton."""
    _logger.info("DisabledPaymentHandler initialized")
    return DisabledPaymentHandler()


def get_payment_handler() -> PaymentHandler:
    """Get the appropriate payment handler based on configuration.

    Returns:
        - SumupPaymentHandler if PAYMENT_TYPE is "SumUp"
        - NFCPaymentHandler if PAYMENT_TYPE is "CocktailBerry"
        - DisabledPaymentHandler if PAYMENT_TYPE is "Disabled"

    """
    match cfg.PAYMENT_TYPE:
        case "Disabled":
            return _get_disabled_payment_handler()
        case "SumUp":
            return get_sumup_payment_handler()
        case "CocktailBerry":
            return get_nfc_payment_handler()
