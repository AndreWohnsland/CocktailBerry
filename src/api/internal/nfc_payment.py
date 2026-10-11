"""NFC payment integration for V2 API."""

import asyncio
from functools import lru_cache

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.logger_handler import LoggerHandler
from src.models import Cocktail, PrepareResult
from src.service import preparation
from src.service.booking import CocktailBooking
from src.service.nfc_payment_service import NFCPaymentService, UserLookup

_logger = LoggerHandler("nfc_payment")


class NFCPaymentHandler:
    """Handler for NFC payment operations."""

    def __init__(self) -> None:
        self._payment_cancelled = False
        self.nfc_service = NFCPaymentService()

    async def start_payment_flow(self, cocktail: Cocktail) -> None:
        """Start the NFC payment flow for a cocktail.

        This method handles:
        1. Setting cocktail status to WAITING_FOR_PAYMENT
        2. Starting NFC polling with timeout
        3. Processing payment on successful NFC scan
        4. Starting cocktail preparation on successful payment
        """
        try:
            await self._payment_flow(cocktail)
        finally:
            # reset after the flow, not before: a cancel that arrives before the flow starts must not be lost
            self._payment_cancelled = False

    async def _payment_flow(self, cocktail: Cocktail) -> None:
        _logger.info("Starting NFC payment flow")
        booking = CocktailBooking.no_user_logged_in()
        shared.cocktail_status.message = booking.message
        shared.cocktail_status.status = PrepareResult.WAITING_FOR_PAYMENT

        booking_in_flight = False

        def nfc_callback(lookup: UserLookup) -> None:
            nonlocal booking, booking_in_flight
            _logger.debug(f"NFC callback triggered with user: {lookup}")
            booking_in_flight = True
            try:
                booking = self.nfc_service.book_cocktail_for_user(lookup, cocktail)
            finally:
                booking_in_flight = False

        self.nfc_service.add_callback("payment_flow", nfc_callback)

        timeout = cfg.PAYMENT_TIMEOUT_S
        elapsed = 0.0
        check_interval = 0.2  # Check every 200ms

        def keep_waiting() -> bool:
            # the booking request runs on the reader thread and debits on completion, so neither a cancel
            # nor the timeout may abandon it while it is in flight
            if booking_in_flight:
                return True
            return (
                elapsed < timeout and booking.result == CocktailBooking.Result.NO_USER and not self._payment_cancelled
            )

        while keep_waiting():
            await asyncio.sleep(check_interval)
            elapsed += check_interval

        self.nfc_service.remove_callback("payment_flow")

        # a booking that landed while the cancel came in has already debited the user, so it wins
        if booking.result != CocktailBooking.Result.SUCCESS:
            if self._payment_cancelled or (elapsed >= timeout):
                booking = CocktailBooking.canceled()
                _logger.debug("Payment cancelled by user")
            else:
                _logger.debug(f"Payment failed: {booking.message}")
            shared.cocktail_status.message = booking.message
            shared.cocktail_status.status = PrepareResult.CANCELED
            return

        _logger.debug("Payment successful, starting cocktail preparation")
        # we will get blocking api call behavior if the callbacks are still fired during preparation
        with self.nfc_service.paused_callbacks():
            await asyncio.to_thread(preparation.prepare_cocktail, cocktail=cocktail, additional_message=booking.message)

        if cfg.PAYMENT_LOGOUT_AFTER_PREPARATION:
            self.nfc_service.logout_user()

    def cancel_payment(self) -> CocktailBooking:
        """Cancel the ongoing payment flow."""
        _logger.debug("Cancelling NFC payment flow")
        self._payment_cancelled = True
        self.nfc_service.remove_callback("payment_flow")
        return CocktailBooking.canceled()

    def get_current_user(self) -> UserLookup:
        """Get the currently logged in user from NFC service."""
        return self.nfc_service.user_lookup


@lru_cache
def get_nfc_payment_handler() -> NFCPaymentHandler:
    """Get or create the global NFC payment handler instance (cached)."""
    return NFCPaymentHandler()
