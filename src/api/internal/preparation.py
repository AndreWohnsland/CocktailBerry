from src.config.config_manager import shared
from src.models import Cocktail, PrepareResult
from src.tabs import maker


def api_addon_prepare_flow(cocktail: Cocktail) -> tuple[bool, str]:
    """Prepare a cocktail in the API UI."""
    result, message, _ = maker.validate_cocktail(cocktail)
    if result != PrepareResult.VALIDATION_OK:
        return False, message
    shared.team_member_name = None
    shared.selected_team = "No Team"
    _, message = maker.prepare_cocktail(cocktail)
    return True, message
