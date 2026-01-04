from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QApplication

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab
from src.config.config_manager import shared as global_shared
from src.display_controller import DP_CONTROLLER
from src.models import Cocktail, PrepareResult
from src.programs.nfc_payment_service import CocktailBooking, NFCPaymentService, User
from src.tabs import bottles, maker

if TYPE_CHECKING:
    from src.ui.setup_custom_dialog import CustomDialog
    from src.ui.setup_mainwindow import MainScreen


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
    if w.cocktail_selection:
        w.cocktail_selection.virgin_checkbox.setChecked(False)
    bottles.set_fill_level_bars(w)
    global_shared.alcohol_factor = 1.0
    w.switch_to_cocktail_list()
    if cfg.PAYMENT_LOGOUT_AFTER_PREPARATION:
        NFCPaymentService().logout_user()
    return True, message


def qt_payment_flow(cocktail: Cocktail) -> CocktailBooking:
    """Run the payment flow in QT UI."""
    if not cfg.PAYMENT_ACTIVE:
        return CocktailBooking.inactive()

    payment_service = NFCPaymentService()
    polling_time = cfg.PAYMENT_TIMEOUT_S
    start_time = time.time()
    dialog: CustomDialog | None = None
    canceled = False
    detected_user: User | None = None

    def on_cancel() -> None:
        nonlocal canceled
        canceled = True

    def on_user_detected(user: User | None, uid: str) -> None:
        """Handle user detection."""
        nonlocal detected_user
        detected_user = user

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
    if dialog is not None:
        with contextlib.suppress(Exception):
            dialog.close()

    if canceled or booking.result == CocktailBooking.Result.NO_USER:
        return CocktailBooking.canceled()
    return booking
