from src.config.config_manager import shared
from src.dialog_handler import DIALOG_HANDLER as DH
from src.machine.controller import claim_machine
from src.models import Cocktail, PrepareResult
from src.tabs import maker


def api_addon_prepare_flow(cocktail: Cocktail) -> tuple[bool, str]:
    """Prepare a cocktail in the API UI."""
    result, message, _ = maker.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        return False, message
    if not claim_machine(PrepareResult.IN_PROGRESS):
        return False, DH.cocktail_in_progress()
    shared.team_member_name = None
    shared.selected_team = "No Team"
    _, message = maker.prepare_cocktail(cocktail)
    return True, message
