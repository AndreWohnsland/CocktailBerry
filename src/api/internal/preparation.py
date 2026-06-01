from src.config.config_manager import shared
from src.logger_handler import LoggerHandler
from src.models import Cocktail, CocktailStatus, HandAddMeasure, PrepareResult
from src.tabs import maker

_logger = LoggerHandler("preparation")

HAND_ADD_TIMEOUT_S = 120
"""Maximum time the background task waits for the user to finish the hand adds before it auto-finishes ,
so a closed browser cannot wedge the machine in the "busy" state forever.
"""


def web_hand_add_runner(cocktail: Cocktail) -> None:
    """v2 runner: surface the hand adds and block until the frontend signals finish.

    The React client drives the per-ingredient tare/read loop and calls the finish endpoint
    (manually or on auto-finish), which sets ``shared.hand_add_finished``.
    """
    hand_adds = [HandAddMeasure(name=i.name, amount=i.amount, unit=i.unit) for i in cocktail.handadds if i.amount > 0]
    shared.hand_add_finished.clear()
    shared.cocktail_status = CocktailStatus(
        progress=100,
        status=PrepareResult.WAITING_FOR_HAND_ADD,
        hand_adds=hand_adds,
    )
    finished = shared.hand_add_finished.wait(timeout=HAND_ADD_TIMEOUT_S)
    if not finished:
        # nobody called finish within the timeout (e.g. the browser was closed); finalize anyway
        # so the machine does not stay locked, but make it visible that this was not user-confirmed
        _logger.warning(
            f"Hand-add phase timed out after {HAND_ADD_TIMEOUT_S}s without a finish signal; "
            f"finalizing '{cocktail.display_name}' automatically."
        )


def api_addon_prepare_flow(cocktail: Cocktail) -> tuple[bool, str]:
    """Prepare a cocktail in the API UI."""
    result, message, _ = maker.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        return False, message
    shared.team_member_name = None
    shared.selected_team = "No Team"
    _, message = maker.prepare_cocktail(cocktail)
    return True, message
