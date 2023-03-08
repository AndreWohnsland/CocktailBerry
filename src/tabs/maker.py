# -*- coding: utf-8 -*-
""" Module with all necessary functions for the maker Tab.
This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from typing import List, Optional, TypeVar
from src.tabs import bottles

from src.database_commander import DB_COMMANDER
from src.error_handler import logerror
from src.models import Cocktail
from src.machine.controller import MACHINE
from src.display_controller import DP_CONTROLLER
from src.service_handler import SERVICE_HANDLER
from src.logger_handler import LoggerHandler
from src.config_manager import CONFIG as cfg

from src.config_manager import shared


_LOGGER = LoggerHandler("maker_module")
T = TypeVar('T', int, float)


def evaluate_recipe_maker_view(w, cocktails: Optional[List[Cocktail]] = None):
    """ Goes through every recipe in the list or all recipes if none given
    Checks if all ingredients are registered, if so, adds it to the list widget
    """
    if cocktails is None:
        cocktails = DB_COMMANDER.get_all_cocktails(get_disabled=False)

    handadds_ids = DB_COMMANDER.get_available_ids()
    available_cocktail_names = [x for x in cocktails if x.is_possible(handadds_ids)]
    DP_CONTROLLER.fill_list_widget_maker(w, available_cocktail_names)


@logerror
def update_shown_recipe(w, clear_view: bool = True):
    """ Updates the maker display Data with the selected recipe"""
    if clear_view:
        DP_CONTROLLER.clear_recipe_data_maker(w)

    cocktail_name, amount, factor = DP_CONTROLLER.get_cocktail_data(w)
    if not cocktail_name:
        return
    cocktail = DB_COMMANDER.get_cocktail(cocktail_name)
    if cocktail is None:
        return
    cocktail.scale_cocktail(amount, factor)
    DP_CONTROLLER.fill_recipe_data_maker(w, cocktail, amount)


def __build_comment_maker(cocktail: Cocktail):
    """Build the additional comment for the completion message (if there are handadds)"""
    comment = ""
    hand_add = cocktail.handadds
    length_desc = sorted(hand_add, key=lambda x: len(x.name), reverse=True)
    for ing in length_desc:
        amount = ing.amount * cfg.EXP_MAKER_FACTOR
        amount = int(amount) if amount >= 8 else round(amount, 1)
        if amount <= 0:
            continue
        comment += f"\n~{amount} {cfg.EXP_MAKER_UNIT} {ing.name}"
    return comment


def __generate_maker_log_entry(cocktail_volume: int, cocktail_name: str, taken_time: float, max_time: float):
    """Enters a log entry for the made cocktail"""
    volume_string = f"{cocktail_volume} ml"
    cancel_log_addition = ""
    if not shared.make_cocktail:
        pumped_volume = round(cocktail_volume * (taken_time) / max_time)
        cancel_log_addition = f" - Recipe canceled at {round(taken_time, 1)} s - {pumped_volume} ml"
    _LOGGER.log_event("INFO", f"{volume_string:6} - {cocktail_name}{cancel_log_addition}")


@logerror
def prepare_cocktail(w):
    """ Prepares a Cocktail, if not already another one is in production and enough ingredients are available"""
    if shared.cocktail_started:
        return
    cocktail_name, cocktail_volume, alcohol_factor = DP_CONTROLLER.get_cocktail_data(w)
    if not cocktail_name:
        DP_CONTROLLER.say_no_recipe_selected()
        return

    # Gets and scales cocktail, check if fill level is enough
    cocktail = DB_COMMANDER.get_cocktail(cocktail_name)
    if cocktail is None:
        return
    cocktail.scale_cocktail(cocktail_volume, alcohol_factor)
    virgin_ending = " (Virgin)" if cocktail.is_virgin else ""
    display_name = f"{cocktail_name}{virgin_ending}"
    error = cocktail.enough_fill_level()
    if error is not None:
        DP_CONTROLLER.say_not_enough_ingredient_volume(*error)
        # Only switch tabs if they are not locked!
        if not cfg.UI_PARTYMODE:
            DP_CONTROLLER.set_tabwidget_tab(w, "bottles")
        return

    print(f"Preparing {cocktail_volume} ml {display_name}")
    # only selects the positions where amount is not 0, if virgin this will remove alcohol from the recipe
    ingredient_bottles = [x.bottle for x in cocktail.machineadds if x.amount > 0]
    ingredient_volumes = [x.amount for x in cocktail.machineadds if x.amount > 0]
    consumption, taken_time, max_time = MACHINE.make_cocktail(
        w, ingredient_bottles, ingredient_volumes, display_name)  # type: ignore
    DB_COMMANDER.increment_recipe_counter(cocktail_name)
    __generate_maker_log_entry(cocktail_volume, display_name, taken_time, max_time)

    # only post if cocktail was made over 50%
    percentage_made = taken_time / max_time
    real_volume = round(cocktail_volume * percentage_made)
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
    DP_CONTROLLER.reset_virgin_setting(w)


def adjust_alcohol(w, amount: float):
    """changes the alcohol factor"""
    new_factor = shared.alcohol_factor + amount
    shared.alcohol_factor = _limit_number(new_factor, 0.7, 1.3)
    update_shown_recipe(w, False)


def adjust_volume(w, amount: int):
    """changes the volume amount"""
    new_volume = shared.cocktail_volume + amount
    shared.cocktail_volume = _limit_number(new_volume, 100, 400)
    update_shown_recipe(w, False)


def _limit_number(val: T, min_val: T, max_val: T) -> T:
    """Limits the number in the boundaries"""
    limited = max(min_val, val)
    limited = min(max_val, limited)
    return limited


def interrupt_cocktail():
    """ Interrupts the cocktail preparation. """
    shared.make_cocktail = False
    print("Canceling!")
