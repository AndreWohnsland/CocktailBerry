from __future__ import annotations

from typing import TYPE_CHECKING

from src.config.config_manager import CONFIG as cfg
from src.display_controller import DP_CONTROLLER
from src.models import Cocktail, PrepareResult
from src.tabs import bottles, maker

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


def qt_prepare_flow(w: MainScreen, cocktail: Cocktail) -> tuple[bool, str]:
    """Prepare a cocktail in the QT UI.

    Switch to the maker screen at the end (if successful).
    Show error/validation message or execute needed actions.
    """
    result, message, _ = maker.validate_cocktail(cocktail)

    # Go to refill dialog, if this window is not locked
    if (result == PrepareResult.NOT_ENOUGH_INGREDIENTS) and (cfg.UI_MAKER_PASSWORD == 0 or not cfg.UI_LOCKED_TABS[2]):
        w.open_refill_dialog(cocktail)
        return False, message

    # No special case: just show the message
    if result != PrepareResult.VALIDATION_OK:
        DP_CONTROLLER.standard_box(message, close_time=60)
        return False, message
    # Only show team dialog if it is enabled
    if cfg.TEAMS_ACTIVE:
        w.open_team_window()

    result, message = maker.prepare_cocktail(cocktail, w)
    # show dialog in case of cancel or if there are handadds
    if result == PrepareResult.CANCELED:
        DP_CONTROLLER.say_cocktail_canceled()
    elif len(cocktail.handadds) > 0:
        DP_CONTROLLER.standard_box(message, close_time=60)

    # Otherwise clean up the rest
    if w.cocktail_selection:
        w.cocktail_selection.virgin_checkbox.setChecked(False)
    bottles.set_fill_level_bars(w)
    DP_CONTROLLER.reset_alcohol_factor()
    w.container_maker.setCurrentWidget(w.cocktail_view)
    return True, message
