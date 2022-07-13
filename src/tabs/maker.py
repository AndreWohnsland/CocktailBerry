# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the maker Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

from typing import List, Optional
from src.tabs import bottles

from src.database_commander import DB_COMMANDER
from src.error_handler import logerror
from src.models import Cocktail
from src.machine.controller import MACHINE
from src.display_controller import DP_CONTROLLER
from src.service_handler import SERVICE_HANDLER
from src.logger_handler import LoggerHandler

from src.config_manager import shared


LOG_HANDLER = LoggerHandler("maker_module", "production_logs")


def evaluate_recipe_maker_view(w, cocktails: Optional[List[Cocktail]] = None):
    """ Goes through every recipe in the list or all recipes if none given
    Checks if all ingredients are registered, if so, adds it to the list widget
    """
    if cocktails is None:
        cocktails = DB_COMMANDER.get_all_cocktails(get_disabled=False)

    handadds_ids = DB_COMMANDER.get_available_ids()
    available_cocktail_names = [x.name for x in cocktails if x.is_possible(handadds_ids)]
    DP_CONTROLLER.fill_list_widget_maker(w, available_cocktail_names)


@logerror
def update_shown_recipe(w, clear_view: bool = True):
    """ Updates the maker display Data with the selected recipe"""
    if clear_view:
        DP_CONTROLLER.clear_recipe_data_maker(w)

    cocktailname, amount, factor = DP_CONTROLLER.get_cocktail_data(w)
    if not cocktailname:
        return
    cocktail = DB_COMMANDER.get_cocktail(cocktailname)
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
        comment += f"\n~{ing.amount:.0f} ml {ing.name}"
    return comment


def __generate_maker_log_entry(cocktail_volume: int, cocktail_name: str, taken_time: float, max_time: float):
    """Enters a log entry for the made cocktail"""
    volume_string = f"{cocktail_volume} ml"
    cancel_log_addition = ""
    if not shared.make_cocktail:
        pumped_volume = round(cocktail_volume * (taken_time) / max_time)
        cancel_log_addition = f" - Recipe canceled at {round(taken_time, 1)} s - {pumped_volume} ml"
    LOG_HANDLER.log_event("INFO", f"{volume_string:6} | {cocktail_name}{cancel_log_addition}")


@logerror
def prepare_cocktail(w):
    """ Prepares a Cocktail, if not already another one is in production and enough ingredients are available"""
    if shared.cocktail_started:
        return
    cocktailname, cocktail_volume, alcohol_faktor = DP_CONTROLLER.get_cocktail_data(w)
    if not cocktailname:
        DP_CONTROLLER.say_no_recipe_selected()
        return

    # Gets and scales cocktail, check if fill level is enough
    cocktail = DB_COMMANDER.get_cocktail(cocktailname)
    if cocktail is None:
        return
    cocktail.scale_cocktail(cocktail_volume, alcohol_faktor)
    error = cocktail.enough_fill_level()
    if error is not None:
        DP_CONTROLLER.say_not_enough_ingredient_volume(*error)
        DP_CONTROLLER.set_tabwidget_tab(w, "bottles")
        return

    print(f"Preparing {cocktail_volume} ml {cocktailname}")
    # only selects the positions where amount is not 0, if virgin this will remove alcohol from the recipe
    ingredient_bottles = [x.bottle for x in cocktail.machineadds if x.amount > 0]
    ingredient_volumes = [x.amount for x in cocktail.machineadds if x.amount > 0]
    consumption, taken_time, max_time = MACHINE.make_cocktail(
        w, ingredient_bottles, ingredient_volumes, cocktailname)
    DB_COMMANDER.increment_recipe_counter(cocktailname)
    __generate_maker_log_entry(cocktail_volume, cocktailname, taken_time, max_time)

    # only post if cocktail was made over 50%
    readiness = taken_time / max_time
    real_volume = round(cocktail_volume * readiness)
    if readiness >= 0.5:
        SERVICE_HANDLER.post_team_data(shared.selected_team, real_volume)
        SERVICE_HANDLER.post_cocktail_to_hook(cocktailname, real_volume, cocktail)

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
    DP_CONTROLLER.reset_alcohol_slider(w)
    shared.cocktail_started = False


def interrupt_cocktail():
    """ Interrupts the cocktail preparation. """
    shared.make_cocktail = False
    print("Canceling Recipe!")
