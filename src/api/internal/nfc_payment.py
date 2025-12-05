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
        shared.cocktail_status.status = PrepareResult.WAITING_FOR_NFC
        self._payment_cancelled = False

        # Set up callback for NFC read
        payment_result: CocktailBooking | None = None

        def nfc_callback(user: User | None, nfc_id: str) -> None:
            nonlocal payment_result
            time_print(f"NFC callback triggered with user: {user}, id: {nfc_id}")
            if user is None:
                payment_result = CocktailBooking.no_user_logged_in()
                return
            payment_result = self.nfc_service.book_cocktail_for_user(user, cocktail)

        self.nfc_service.add_callback(nfc_callback)

        # Wait for NFC scan or timeout
        timeout = cfg.PAYMENT_TIMEOUT_S
        elapsed = 0.0
        check_interval = 0.2  # Check every 200ms

        try:
            while elapsed < timeout and payment_result is None and not self._payment_cancelled:
                await asyncio.sleep(check_interval)
                elapsed += check_interval

            # Clean up callback
            self.nfc_service.clear_callback()

            # Handle the result
            if self._payment_cancelled:
                time_print("Payment cancelled by user")
                shared.cocktail_status.status = PrepareResult.CANCELED
                shared.cocktail_status.message = "Payment cancelled"
                return

            if payment_result is None:
                time_print("Payment timeout - no NFC tag detected")
                shared.cocktail_status.status = PrepareResult.CANCELED
                shared.cocktail_status.message = "Payment timeout - please scan your NFC tag"
                return

            if payment_result.result != CocktailBooking.Result.SUCCESS:
                time_print(f"Payment failed: {payment_result.message}")
                shared.cocktail_status.status = PrepareResult.CANCELED
                shared.cocktail_status.message = payment_result.message
                return

            # Payment successful, prepare cocktail
            time_print("Payment successful, starting cocktail preparation")
            result, message = await asyncio.to_thread(maker.prepare_cocktail, cocktail)
            # The cocktail status is already set by prepare_cocktail
            time_print(f"Cocktail preparation completed with result: {result}, message: {message}")

        except Exception as e:
            time_print(f"Error in payment flow: {e}")
            self.nfc_service.clear_callback()
            shared.cocktail_status.status = PrepareResult.CANCELED
            shared.cocktail_status.message = f"Payment error: {e!s}"

    def cancel_payment(self) -> None:
        """Cancel the ongoing payment flow."""
        time_print("Cancelling NFC payment flow")
        self._payment_cancelled = True
        self.nfc_service.clear_callback()

    def get_current_user(self) -> User | None:
        """Get the currently logged in user from NFC service."""
        uid = self.nfc_service.uid
        if uid is None:
            return None
        return self.nfc_service.get_user_for_id(uid)


@lru_cache(maxsize=1)
def get_nfc_payment_handler() -> NFCPaymentHandler:
    """Get or create the global NFC payment handler instance (cached)."""
    return NFCPaymentHandler()
