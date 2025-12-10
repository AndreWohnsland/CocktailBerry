"""NFC payment integration for V2 API."""

import asyncio
from functools import lru_cache

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.models import Cocktail, PrepareResult
from src.programs.nfc_payment_service import CocktailBooking, NFCPaymentService, User
from src.tabs import maker
from src.utils import time_print


class NFCPaymentHandler:
    """Handler for NFC payment operations."""

    def __init__(self) -> None:
        self._payment_cancelled = False
        self.nfc_service = NFCPaymentService()

    async def start_payment_flow(self, cocktail: Cocktail) -> None:
        """Start the NFC payment flow for a cocktail.

        This method handles:
        1. Setting cocktail status to WAITING_FOR_NFC
        2. Starting NFC polling with timeout
        3. Processing payment on successful NFC scan
        4. Starting cocktail preparation on successful payment
        """
        time_print("Starting NFC payment flow")
        booking = CocktailBooking.no_user_logged_in()
        shared.cocktail_status.message = booking.message
        shared.cocktail_status.status = PrepareResult.WAITING_FOR_NFC
        self._payment_cancelled = False

        def nfc_callback(user: User | None, nfc_id: str) -> None:
            nonlocal booking
            time_print(f"NFC callback triggered with user: {user}, id: {nfc_id}")
            booking = self.nfc_service.book_cocktail_for_user(user, cocktail)

        self.nfc_service.add_callback("payment_flow", nfc_callback)

        timeout = cfg.PAYMENT_TIMEOUT_S
        elapsed = 0.0
        check_interval = 0.2  # Check every 200ms

        while (
            (elapsed < timeout) and (booking.result == CocktailBooking.Result.NO_USER) and (not self._payment_cancelled)
        ):
            await asyncio.sleep(check_interval)
            elapsed += check_interval

        self.nfc_service.remove_callback("payment_flow")

        if self._payment_cancelled or (elapsed >= timeout):
            booking = CocktailBooking.canceled()
            time_print("Payment cancelled by user")
            shared.cocktail_status.message = booking.message
            shared.cocktail_status.status = PrepareResult.CANCELED
            return

        if booking.result != CocktailBooking.Result.SUCCESS:
            time_print(f"Payment failed: {booking.message}")
            shared.cocktail_status.status = PrepareResult.CANCELED
            shared.cocktail_status.message = booking.message
            return

        time_print("Payment successful, starting cocktail preparation")
        # we will get blocking api call behavior if the callbacks are still fired during preparation
        with self.nfc_service.paused_callbacks():
            await asyncio.to_thread(maker.prepare_cocktail, cocktail)

        if cfg.PAYMENT_LOGOUT_AFTER_PREPARATION:
            self.nfc_service.logout_user()

    def cancel_payment(self) -> CocktailBooking:
        """Cancel the ongoing payment flow."""
        time_print("Cancelling NFC payment flow")
        self._payment_cancelled = True
        self.nfc_service.remove_callback("payment_flow")
        return CocktailBooking.canceled()

    def get_current_user(self) -> User | None:
        """Get the currently logged in user from NFC service."""
        return self.nfc_service.user


@lru_cache
def get_nfc_payment_handler() -> NFCPaymentHandler:
    """Get or create the global NFC payment handler instance (cached)."""
    return NFCPaymentHandler()
