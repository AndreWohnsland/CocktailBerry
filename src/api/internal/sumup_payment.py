"""SumUp payment integration for V2 API."""

import asyncio
from functools import lru_cache

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.logger_handler import LoggerHandler
from src.models import Cocktail, PrepareResult
from src.service.booking import CocktailBooking
from src.service.sumup_payment_service import Err, SumupPaymentService
from src.tabs import maker

_logger = LoggerHandler("sumup_payment")


class SumupPaymentHandler:
    """Handler for SumUp payment operations."""

    def __init__(self) -> None:
        self._payment_cancelled = False
        self.sumup_service = SumupPaymentService(
            api_key=cfg.PAYMENT_SUMUP_API_KEY,
            merchant_code=cfg.PAYMENT_SUMUP_MERCHANT_CODE,
        )

    async def start_payment_flow(self, cocktail: Cocktail) -> None:
        """Start the SumUp payment flow for a cocktail.

        This method handles:
        1. Setting cocktail status to WAITING_FOR_PAYMENT
        2. Triggering a checkout on the SumUp terminal
        3. Polling for completion
        4. Starting cocktail preparation on successful payment
        """
        _logger.info("Starting SumUp payment flow")
        shared.cocktail_status.message = CocktailBooking.sumup_waiting_for_payment().message
        shared.cocktail_status.status = PrepareResult.WAITING_FOR_PAYMENT
        self._payment_cancelled = False

        # Calculate price
        multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if cocktail.is_virgin else 1.0
        price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, price_multiplier=multiplier)
        # SumUp uses minor units (cents), so multiply by 100
        value_in_cents = int(price * 100)

        reader_id = cfg.PAYMENT_SUMUP_TERMINAL_ID
        if not reader_id:
            _logger.error("No SumUp terminal ID configured")
            shared.cocktail_status.status = PrepareResult.CANCELED
            shared.cocktail_status.message = CocktailBooking.sumup_no_terminal().message
            return

        # Trigger checkout on terminal
        checkout_result = self.sumup_service.trigger_checkout(
            reader_id=reader_id,
            value=value_in_cents,
            description=f"CocktailBerry: {cocktail.name}",
        )

        if isinstance(checkout_result, Err):
            _logger.error(f"Failed to trigger checkout: {checkout_result.error}")
            shared.cocktail_status.status = PrepareResult.CANCELED
            shared.cocktail_status.message = CocktailBooking.sumup_checkout_failed().message
            return

        client_transaction_id: str = checkout_result.data
        _logger.debug(f"Checkout triggered, transaction ID: {client_transaction_id}")

        # Wait for completion (run in thread to not block)
        await asyncio.to_thread(
            self.sumup_service.wait_for_complete,
            reader_id,
            poll_interval_s=1.0,
            timeout_s=cfg.PAYMENT_TIMEOUT_S,
        )

        if self._payment_cancelled:
            _logger.debug("Payment cancelled by user")
            shared.cocktail_status.message = CocktailBooking.canceled().message
            shared.cocktail_status.status = PrepareResult.CANCELED
            return

        # Check transaction result
        transaction_result = self.sumup_service.get_transaction(client_transaction_id)
        if isinstance(transaction_result, Err):
            _logger.error(f"Failed to get transaction: {transaction_result.error}")
            shared.cocktail_status.status = PrepareResult.CANCELED
            shared.cocktail_status.message = CocktailBooking.sumup_checkout_failed().message
            return

        transaction = transaction_result.data
        if transaction.status != "SUCCESSFUL":
            _logger.warning(f"Transaction not successful: {transaction.status}")
            shared.cocktail_status.status = PrepareResult.CANCELED
            shared.cocktail_status.message = CocktailBooking.sumup_payment_declined().message
            return

        _logger.debug("Payment successful, starting cocktail preparation")
        booking = CocktailBooking.sumup_successful()
        await asyncio.to_thread(maker.prepare_cocktail, cocktail=cocktail, additional_message=booking.message)

    def cancel_payment(self) -> CocktailBooking:
        """Cancel the ongoing payment flow."""
        _logger.debug("Cancelling SumUp payment flow")
        self._payment_cancelled = True
        reader_id = cfg.PAYMENT_SUMUP_TERMINAL_ID
        if reader_id:
            self.sumup_service.terminate_checkout(reader_id)
        return CocktailBooking.canceled()


@lru_cache
def get_sumup_payment_handler() -> SumupPaymentHandler:
    """Get or create the global SumUp payment handler instance (cached)."""
    return SumupPaymentHandler()
