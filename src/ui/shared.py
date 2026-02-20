from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QEventLoop
from PyQt6.QtWidgets import QApplication

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.models import Cocktail, PrepareResult
from src.service.booking import CocktailBooking
from src.service.nfc_payment_service import NFCPaymentService, UserLookup
from src.service.sumup_payment_service import Err, SumupPaymentService
from src.tabs import bottles, maker
from src.ui.qt_worker import run_with_spinner

if TYPE_CHECKING:
    from src.ui.setup_custom_dialog import CustomDialog
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("QtPrepareFlow")


def qt_prepare_flow(w: MainScreen, cocktail: Cocktail) -> tuple[bool, str]:
    """Prepare a cocktail in the QT UI.

    Switch to the maker screen at the end (if successful).
    Show error/validation message or execute needed actions.
    """
    result, message, _ = maker.validate_cocktail(cocktail)

    # Go to refill dialog, if this window is not locked
    if (result == PrepareResult.NOT_ENOUGH_INGREDIENTS) and (
        cfg.UI_MAKER_PASSWORD == 0 or not cfg.UI_LOCKED_TABS[Tab.BOTTLES]
    ):
        w.open_refill_dialog(cocktail)
        return False, message

    # No special case: just show the message
    if result != PrepareResult.VALIDATION_OK:
        DP_CONTROLLER.standard_box(message, close_time=60)
        return False, message
    # Only show team dialog if it is enabled
    if cfg.TEAMS_ACTIVE:
        w.open_team_window()

    booking = qt_payment_flow(cocktail)
    if booking.result not in [
        CocktailBooking.Result.SUCCESS,
        CocktailBooking.Result.INACTIVE,
    ]:
        DP_CONTROLLER.standard_box(booking.message, close_time=60)
        return False, booking.message

    additional_message = "" if booking.result == CocktailBooking.Result.INACTIVE else booking.message
    result, message = maker.prepare_cocktail(cocktail, w, additional_message)
    # show dialog in case of cancel or if there are handadds
    if result == PrepareResult.CANCELED:
        DP_CONTROLLER.say_cocktail_canceled()
    elif len(message) > 0:
        DP_CONTROLLER.standard_box(message, close_time=60)

    # Otherwise clean up the rest
    bottles.set_fill_level_bars(w)
    w.switch_to_cocktail_list()
    if cfg.cocktailberry_payment and cfg.PAYMENT_LOGOUT_AFTER_PREPARATION:
        NFCPaymentService().logout_user()
    return True, message


def qt_payment_flow(cocktail: Cocktail) -> CocktailBooking:
    """Run the payment flow in QT UI."""
    match cfg.PAYMENT_TYPE:
        case "Disabled":
            return CocktailBooking.inactive()
        case "SumUp":
            return sumup_payment_flow(cocktail)
        case "CocktailBerry":
            return cocktailberry_payment_flow(cocktail)


def sumup_payment_flow(cocktail: Cocktail) -> CocktailBooking:  # noqa: PLR0911
    """Run the SumUp payment flow for qt."""
    multiplier = cfg.PAYMENT_VIRGIN_MULTIPLIER / 100 if cocktail.is_virgin else 1.0
    price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, price_multiplier=multiplier)
    value_in_cents = int(price * 100)
    if value_in_cents <= 0:
        _logger.info(f"Skipping SumUp checkout for free cocktail '{cocktail.name}'")
        return CocktailBooking.inactive()

    reader_id = cfg.PAYMENT_SUMUP_TERMINAL_ID
    if not reader_id:
        return CocktailBooking.sumup_no_terminal()

    sumup_service = SumupPaymentService(
        api_key=cfg.PAYMENT_SUMUP_API_KEY,
        merchant_code=cfg.PAYMENT_SUMUP_MERCHANT_CODE,
    )

    # Trigger checkout on terminal
    checkout_result = sumup_service.trigger_checkout(
        reader_id=reader_id,
        value=value_in_cents,
        description=f"CocktailBerry: {cocktail.name}",
    )

    if isinstance(checkout_result, Err):
        _logger.error(f"Failed to trigger checkout: {checkout_result.error}")
        return CocktailBooking.sumup_checkout_failed()

    client_transaction_id = checkout_result.data
    canceled = False
    dialog: CustomDialog | None = None
    event_loop = QEventLoop()

    def on_cancel() -> None:
        nonlocal canceled
        canceled = True
        sumup_service.terminate_checkout(reader_id)
        event_loop.quit()

    def on_wait_complete(_result: object) -> None:
        """Quit event loop when worker finishes."""
        event_loop.quit()

    # Show waiting dialog
    dialog = DP_CONTROLLER.standard_box_non_blocking(
        CocktailBooking.sumup_waiting_for_payment().message,
        close_callback=on_cancel,
    )

    # Create worker with spinner (non-blocking parent so cancel button works)
    worker = run_with_spinner(
        lambda: sumup_service.wait_for_complete(
            reader_id,
            poll_interval_s=1.0,
            timeout_s=cfg.PAYMENT_TIMEOUT_S,
        ),
        parent=dialog,
        on_finish=on_wait_complete,
        disable_parent=False,
    )

    # Process Qt events while waiting for worker to finish
    event_loop.exec()
    # Ensure worker is finished before continuing
    worker.wait()

    if canceled:
        _close_dialog_safe(dialog)
        return CocktailBooking.canceled()

    # Check transaction result
    transaction_result = sumup_service.get_transaction(client_transaction_id)
    _close_dialog_safe(dialog)
    if isinstance(transaction_result, Err):
        _logger.error(f"Error fetching transaction result: {transaction_result.error}")
        return CocktailBooking.sumup_checkout_failed()

    if transaction_result.data.status != "SUCCESSFUL":
        return CocktailBooking.sumup_payment_declined()

    return CocktailBooking.sumup_successful()


def cocktailberry_payment_flow(cocktail: Cocktail) -> CocktailBooking:
    """Run the cocktailberry payment flow for qt."""
    payment_service = NFCPaymentService()
    polling_time = cfg.PAYMENT_TIMEOUT_S
    start_time = time.time()
    dialog: CustomDialog | None = None
    canceled = False
    detected_user: UserLookup = UserLookup.removed()

    def on_cancel() -> None:
        nonlocal canceled
        canceled = True

    def on_user_detected(lookup: UserLookup) -> None:
        """Handle user detection."""
        nonlocal detected_user
        detected_user = lookup

    payment_service.add_callback("payment_flow", on_user_detected)
    # Try to book immediately if we have a user
    booking = payment_service.book_cocktail_for_user(detected_user, cocktail)

    if booking.result == CocktailBooking.Result.NO_USER:
        dialog = DP_CONTROLLER.standard_box_non_blocking(
            booking.message, close_time=polling_time, close_callback=on_cancel
        )

    while (
        (booking.result == CocktailBooking.Result.NO_USER)
        and (time.time() - start_time < polling_time)
        and not canceled
    ):
        QApplication.processEvents()
        time.sleep(0.2)
        booking = payment_service.book_cocktail_for_user(detected_user, cocktail)

    payment_service.remove_callback("payment_flow")
    _close_dialog_safe(dialog)

    if canceled or booking.result == CocktailBooking.Result.NO_USER:
        return CocktailBooking.canceled()
    return booking


def _close_dialog_safe(dialog: CustomDialog | None) -> None:
    """Close a dialog safely, ignoring exceptions."""
    if dialog is not None:
        with contextlib.suppress(Exception):
            dialog.close()
