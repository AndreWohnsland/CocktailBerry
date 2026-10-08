import copy

from src.config.config_manager import CONFIG as cfg
from src.models import Cocktail
from src.service.nfc_payment_service import User


def filter_cocktails_by_user(user: User | None, cocktails: list[Cocktail]) -> list[Cocktail]:
    # if operator wants to have implicit filtering, they should use lock screen
    # since this will enforce a user at cocktail view
    if user is None:
        return cocktails
    filtered = []
    lowest_amount = min(cfg.MAKER_PREPARE_VOLUME) if cfg.MAKER_PREPARE_VOLUME else None
    for cocktail in cocktails:
        cocktail_amount = cocktail.amount
        if not cfg.MAKER_USE_RECIPE_VOLUME and lowest_amount is not None:
            cocktail_amount = lowest_amount
        # a minor may only have cocktails that can be served without alcohol, and only that way
        cocktail.is_allowed = True
        if not user.is_adult and not (cocktail.virgin_available or cocktail.is_naturally_virgin):
            cocktail.is_allowed = False
            filtered.append(copy.deepcopy(cocktail))
            continue
        if not user.is_adult:
            cocktail.only_virgin = True
        # the recipe is unscaled here, so tell the price what the user would be served
        price = cocktail.current_price(
            cfg.PAYMENT_PRICE_ROUNDING,
            cocktail_amount,
            virgin_multiplier=cfg.PAYMENT_VIRGIN_MULTIPLIER / 100,
            as_virgin=not user.is_adult,
        )
        if user.balance < price:
            cocktail.is_allowed = False
        filtered.append(copy.deepcopy(cocktail))
    return filtered
