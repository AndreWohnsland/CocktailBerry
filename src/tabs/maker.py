"""Module with all necessary functions for the maker Tab.

This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from __future__ import annotations

from typing import Any

from src.config_manager import CONFIG as cfg
from src.config_manager import shared
from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.error_handler import logerror
from src.logger_handler import LoggerHandler
from src.machine.controller import MACHINE
from src.models import Cocktail
from src.programs.addons import ADDONS
from src.service_handler import SERVICE_HANDLER
from src.tabs import bottles
from src.ui.setup_refill_dialog import RefillDialog
from src.utils import time_print

_LOGGER = LoggerHandler("maker_module")


def __build_comment_maker(cocktail: Cocktail):
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


def __generate_maker_log_entry(cocktail_volume: int, cocktail_name: str, taken_time: float, max_time: float):
    """Enter a log entry for the made cocktail."""
    volume_string = f"{cocktail_volume} ml"
    cancel_log_addition = ""
    if not shared.make_cocktail:
        pumped_volume = round(cocktail_volume * (taken_time) / max_time)
        cancel_log_addition = f" - Recipe canceled at {round(taken_time, 1)} s - {pumped_volume} ml"
    _LOGGER.log_event("INFO", f"{volume_string:6} - {cocktail_name}{cancel_log_addition}")


@logerror
def prepare_cocktail(w, cocktail: Cocktail | None = None):
    """Prepare a Cocktail, if not already another one is in production and enough ingredients are available."""
    if shared.cocktail_started:
        return False
    # Gets and scales cocktail, check if fill level is enough
    if cocktail is None:
        return False
    virgin_ending = " (Virgin)" if cocktail.is_virgin else ""
    display_name = f"{cocktail.name}{virgin_ending}"
    empty_ingredient = None
    # only do check if this option is activated
    if cfg.MAKER_CHECK_BOTTLE:
        empty_ingredient = cocktail.enough_fill_level()
    if empty_ingredient is not None:
        # either show only the message (if bottles window is locked) or show also the refill prompt
        if cfg.UI_MAKER_PASSWORD == 0 or not cfg.UI_LOCKED_TABS[2]:
            refill_window = RefillDialog(w, empty_ingredient)
            refill_window.exec_()
        else:
            DP_CONTROLLER.say_not_enough_ingredient_volume(
                empty_ingredient.name, empty_ingredient.fill_level, empty_ingredient.amount
            )
        return False

    # only selects the positions where amount is not 0, if virgin this will remove alcohol from the recipe
    ingredient_bottles = [x for x in cocktail.machineadds if x.amount > 0]

    # Runs addons before hand, check if they throw an error
    addon_data: dict[str, Any] = {"cocktail": cocktail}
    try:
        ADDONS.before_cocktail(addon_data)
    except RuntimeError as err:
        DP_CONTROLLER.standard_box(str(err))
        return False

    # Now make the cocktail
    time_print(f"Preparing {cocktail.adjusted_amount} ml {display_name}")
    consumption, taken_time, max_time = MACHINE.make_cocktail(w, ingredient_bottles, display_name)
    DB_COMMANDER.increment_recipe_counter(cocktail.name)
    __generate_maker_log_entry(cocktail.adjusted_amount, display_name, taken_time, max_time)

    # run Addons after cocktail preparation
    addon_data["consumption"] = consumption
    ADDONS.after_cocktail(addon_data)

    # only post if cocktail was made over 50%
    percentage_made = taken_time / max_time
    real_volume = round(cocktail.adjusted_amount * percentage_made)
    if percentage_made >= 0.5:
        SERVICE_HANDLER.post_team_data(shared.selected_team, real_volume, shared.team_member_name)
        SERVICE_HANDLER.post_cocktail_to_hook(display_name, real_volume, cocktail)

    # the cocktail was canceled!
    if not shared.make_cocktail:
        consumption_names = [x.name for x in cocktail.machineadds]
        consumption_amount = consumption
        DB_COMMANDER.set_multiple_ingredient_consumption(consumption_names, consumption_amount)
        DP_CONTROLLER.say_cocktail_canceled()
    else:
        consumption_names = [x.name for x in cocktail.adjusted_ingredients]
        consumption_amount = [x.amount for x in cocktail.adjusted_ingredients]
        DB_COMMANDER.set_multiple_ingredient_consumption(consumption_names, consumption_amount)
        comment = __build_comment_maker(cocktail)
        DP_CONTROLLER.say_cocktail_ready(comment)

    bottles.set_fill_level_bars(w)
    DP_CONTROLLER.reset_alcohol_factor()
    return True


def interrupt_cocktail():
    """Interrupts the cocktail preparation."""
    shared.make_cocktail = False
    time_print("Canceling the cocktail!")
