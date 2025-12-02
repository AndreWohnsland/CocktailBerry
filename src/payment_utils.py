import copy

from src.config.config_manager import CONFIG as cfg
from src.models import Cocktail
from src.programs.nfc_payment_service import User


def filter_cocktails_by_user(user: User | None, cocktails: list[Cocktail]) -> list[Cocktail]:
    # if operator wants to have implicit filtering, they should use lock screen
    # since this will enforce a user at cocktail view
    if user is None:
        return cocktails
    filtered = []
    lowest_amount = cfg.MAKER_PREPARE_VOLUME[0] if cfg.MAKER_PREPARE_VOLUME else None
    for cocktail in cocktails:
        cocktail_amount = cocktail.amount
        if not cfg.MAKER_USE_RECIPE_VOLUME and lowest_amount is not None:
            cocktail_amount = lowest_amount
        # if user not allowed alcohol, only disallow the cocktail if it's virgin available, set only virgin flag
        # otherwise disallow the cocktail
        # for other users, just use the regular price calculation
        cocktail.is_allowed = True
        if not user.can_get_alcohol and not cocktail.virgin_available:
            cocktail.is_allowed = False
            filtered.append(copy.deepcopy(cocktail))
            continue
        price = cocktail.current_price(cfg.PAYMENT_PRICE_ROUNDING, cocktail_amount)
        if not user.can_get_alcohol and cocktail.virgin_available:
            cocktail.only_virgin = True
            price = cocktail.current_price(
                cfg.PAYMENT_PRICE_ROUNDING, cocktail_amount, price_multiplier=cfg.PAYMENT_VIRGIN_MULTIPLIER / 100
            )
        if user.balance < price:
            cocktail.is_allowed = False
        filtered.append(copy.deepcopy(cocktail))
    return filtered
