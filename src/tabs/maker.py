"""Module with all necessary functions for the maker Tab.

This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.models import Cocktail, CocktailStatus, Ingredient, PrepareResult
from src.programs.addons import ADDONS
from src.service_handler import SERVICE_HANDLER
from src.utils import time_print

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("maker_module")


def _build_comment_maker(cocktail: Cocktail):
    """Build the additional comment for the completion message (if there are handadds)."""
    comment = ""
    hand_add = cocktail.handadds
    # sort by descending length of the name and unit combined
    length_desc = sorted(hand_add, key=lambda x: len(x.name) + len(x.unit), reverse=True)
    for ing in length_desc:
        amount = ing.amount
        if ing.unit != "ml":
            amount = ing.amount * cfg.EXP_MAKER_FACTOR
        # usually show decimal places, up to 8, but if not ml is used clip decimal place
        threshold = 8 if ing.unit == "ml" else 0
        amount = int(round(amount, 1)) if amount >= threshold else round(amount, 1)
        if amount <= 0:
            continue
        unit = cfg.EXP_MAKER_UNIT if ing.unit == "ml" else ing.unit
        comment += f"\n~{amount} {unit} {ing.name}"

    return comment


def _log_cocktail(cocktail_volume: int, real_volume: int, cocktail_name: str, taken_time: float):
    """Enter a log entry for the made cocktail."""
    volume_string = f"{cocktail_volume} ml"
    cancel_log_addition = ""
    if shared.cocktail_status.status == PrepareResult.CANCELED:
        cancel_log_addition = f" - Recipe canceled at {round(taken_time, 1)} s - {real_volume} ml"
    _logger.log_event("INFO", f"{volume_string:6} - {cocktail_name}{cancel_log_addition}")


def prepare_cocktail(cocktail: Cocktail, w: MainScreen | None = None) -> tuple[PrepareResult, str]:
    """Prepare a Cocktail, if not already another one is in production and enough ingredients are available."""
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    addon_data: dict[str, Any] = {"cocktail": cocktail}

    # only selects the positions where amount is not 0, if virgin this will remove alcohol from the recipe
    ingredient_bottles = [x for x in cocktail.machineadds if x.amount > 0]

    # Now make the cocktail
    display_name = f"{cocktail.name} (Virgin)" if cocktail.is_virgin else cocktail.name
    time_print(f"Preparing {cocktail.adjusted_amount} ml {display_name}")
    add_message = DH.cocktail_ready(_build_comment_maker(cocktail))
    canceled_message = DH.get_translation("cocktail_canceled")
    consumption, taken_time, max_time = MACHINE.make_cocktail(
        w, ingredient_bottles, display_name, finish_message=add_message
    )
    DBC = DatabaseCommander()
    DBC.increment_recipe_counter(cocktail.name)

    percentage_made = taken_time / max_time
    real_volume = round(cocktail.adjusted_amount * percentage_made)
    _log_cocktail(cocktail.adjusted_amount, real_volume, display_name, taken_time)

    # run Addons after cocktail preparation
    addon_data["consumption"] = consumption
    ADDONS.after_cocktail(addon_data)

    # only post if cocktail was made over 50%
    if percentage_made >= 0.5:
        SERVICE_HANDLER.post_team_data(shared.selected_team, real_volume, shared.team_member_name)
        SERVICE_HANDLER.post_cocktail_to_hook(display_name, real_volume, cocktail)

    # the cocktail was canceled!
    if shared.cocktail_status.status == PrepareResult.CANCELED:
        consumption_names = [x.name for x in cocktail.machineadds]
        consumption_amount = consumption
        DBC.set_multiple_ingredient_consumption(consumption_names, consumption_amount)
        return PrepareResult.CANCELED, canceled_message

    shared.cocktail_status.status = PrepareResult.FINISHED
    consumption_names = [x.name for x in cocktail.adjusted_ingredients]
    consumption_amount = [x.amount for x in cocktail.adjusted_ingredients]
    DBC.set_multiple_ingredient_consumption(consumption_names, consumption_amount)

    return PrepareResult.FINISHED, add_message


def interrupt_cocktail():
    """Interrupts the cocktail preparation."""
    shared.cocktail_status.status = PrepareResult.CANCELED
    time_print("Canceling the cocktail!")


def validate_cocktail(cocktail: Cocktail) -> tuple[PrepareResult, str, Ingredient | None]:
    """Validate the cocktail.

    Returns the validator code | Error message (in case of addon).
    """
    addon_data: dict[str, Any] = {"cocktail": cocktail}
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        return PrepareResult.IN_PROGRESS, DH.cocktail_in_progress(), None
    empty_ingredient = None
    if cfg.MAKER_CHECK_BOTTLE:
        empty_ingredient = cocktail.enough_fill_level()
    if empty_ingredient is not None:
        msg = DH.not_enough_ingredient_volume(
            empty_ingredient.name,
            empty_ingredient.fill_level,
            empty_ingredient.amount,
        )
        if cfg.UI_MAKER_PASSWORD != 0 and cfg.UI_LOCKED_TABS[2]:
            msg += f' \n\n{DH.get_translation("bottle_tab_locked")}'
        return PrepareResult.NOT_ENOUGH_INGREDIENTS, msg, empty_ingredient
    try:
        ADDONS.before_cocktail(addon_data)
    except RuntimeError as err:
        return PrepareResult.ADDON_ERROR, str(err), None

    return PrepareResult.VALIDATION_OK, "", None


def calibrate(bottle_number: int, amount: int):
    """Calibrate a bottle."""
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    display_name = f"{amount} ml volume, pump #{bottle_number}"
    ing = Ingredient(
        id=0,
        name="Calibration",
        alcohol=0,
        bottle_volume=1000,
        fill_level=1000,
        hand=False,
        pump_speed=100,
        amount=amount,
        bottle=bottle_number,
    )
    MACHINE.make_cocktail(
        w=None,
        ingredient_list=[ing],
        recipe=display_name,
        is_cocktail=False,
        verbose=False,
    )


def prepare_ingredient(ingredient: Ingredient, w: MainScreen | None = None):
    """Prepare an ingredient."""
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    time_print(f"Spending {ingredient.amount} ml {ingredient.name}")
    made_volume, _, _ = MACHINE.make_cocktail(w, [ingredient], ingredient.name, False)
    consumed_volume = made_volume[0]
    DBC = DatabaseCommander()
    DBC.increment_ingredient_consumption(ingredient.name, consumed_volume)
    volume_string = f"{consumed_volume} ml"
    _logger.log_event("INFO", f"{volume_string:6} | {ingredient.name}")
