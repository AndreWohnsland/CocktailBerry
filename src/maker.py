# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the maker Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

from src.bottles import set_fill_level_bars
from src.error_suppression import logerror

from src.database_commander import DB_COMMANDER
from src.models import Cocktail
from src.rpi_controller import RPI_CONTROLLER
from src.display_controller import DP_CONTROLLER
from src.service_handler import SERVICE_HANDLER
from src.logger_handler import LoggerHandler

from config.config_manager import shared


LOG_HANDLER = LoggerHandler("maker_module", "production_logs")


@logerror
def refresh_recipe_maker_view(w, possible_recipes_id=None):
    """ Goes through every recipe in the list or all recipes if none given
    Checks if all ingredients are registered, if so, adds it to the list widget
    """
    if possible_recipes_id is None:
        possible_recipes_id = DB_COMMANDER.get_enabled_recipes_id()

    available_recipes_ids = []
    bottle_ids = set(DB_COMMANDER.get_ids_at_bottles())
    handadds_ids = set(DB_COMMANDER.get_handadd_ids())

    for recipe_id in possible_recipes_id:
        recipe_handadds, recipe_machineadds = DB_COMMANDER.get_ingredients_seperated_by_handadd(recipe_id)
        recipe_handadds = set(recipe_handadds)
        recipe_machineadds = set(recipe_machineadds)

        if (not recipe_handadds.issubset(handadds_ids)) or (not recipe_machineadds.issubset(bottle_ids)):
            continue

        available_recipes_ids.append(recipe_id)

    recipe_names = DB_COMMANDER.get_multiple_recipe_names_from_ids(available_recipes_ids)
    DP_CONTROLLER.fill_list_widget_maker(w, recipe_names)


@logerror
def update_shown_recipe(w):
    """ Updates the maker display Data with the selected recipe"""
    cocktailname, amount, factor = DP_CONTROLLER.get_cocktail_data(w)
    if not cocktailname:
        return

    DP_CONTROLLER.clear_recipe_data_maker(w)
    cocktail = DB_COMMANDER.get_cocktail(cocktailname)
    cocktail.scale_cocktail(amount, factor)
    DP_CONTROLLER.fill_recipe_data_maker(w, cocktail, amount)


def __build_comment_maker(cocktail: Cocktail):
    """Build the additional comment for the completion message (if there are handadds)"""
    comment = ""
    hand_add = cocktail.get_handadds()
    length_desc = sorted(hand_add, key=lambda x: len(x.name), reverse=True)
    for ing in length_desc:
        comment += f"\n~{ing.amount:.0f} ml {ing.name}"
    return comment


def __generate_maker_log_entry(cocktail_volume, cocktail_name, taken_time, max_time):
    """Enters a log entry for the made cocktail"""
    volume_string = f"{cocktail_volume} ml"
    cancel_log_addition = ""
    if not shared.make_cocktail:
        pumped_volume = round(cocktail_volume * (taken_time) / max_time)
        cancel_log_addition = f" - Recipe canceled at {round(taken_time, 1)} s - {pumped_volume} ml"
    LOG_HANDLER.log_event("INFO", f"{volume_string:8} | {cocktail_name}{cancel_log_addition}")


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
    cocktail.scale_cocktail(cocktail_volume, alcohol_faktor)
    error = cocktail.enough_fill_level()
    if error is not None:
        DP_CONTROLLER.say_not_enough_ingredient_volume(*error)
        DP_CONTROLLER.set_tabwidget_tab(w, "bottles")
        return

    print(f"Preparing {cocktail_volume} ml {cocktailname}")
    ingredient_bottles = [x.bottle for x in cocktail.get_machineadds()]
    ingredient_volumes = [x.amount for x in cocktail.get_machineadds()]
    consumption, taken_time, max_time = RPI_CONTROLLER.make_cocktail(
        w, ingredient_bottles, ingredient_volumes, cocktailname)
    DB_COMMANDER.set_recipe_counter(cocktailname)
    __generate_maker_log_entry(cocktail_volume, cocktailname, taken_time, max_time)

    # only post if cocktail was made over 50%
    readiness = taken_time / max_time
    real_volume = round(cocktail_volume * readiness)
    if readiness >= 0.5:
        SERVICE_HANDLER.post_team_data(shared.selected_team, real_volume)
        SERVICE_HANDLER.post_cocktail_to_hook(cocktailname, real_volume)

    # the cocktail was canceled!
    if not shared.make_cocktail:
        consumption_names = [x.name for x in cocktail.get_machineadds()]
        consumption_amount = consumption
        DB_COMMANDER.set_multiple_ingredient_consumption(consumption_names, consumption_amount)
        DP_CONTROLLER.say_cocktail_canceled()
    else:
        consumption_names = [x.name for x in cocktail.adjusted_ingredients]
        consumption_amount = [x.amount for x in cocktail.adjusted_ingredients]
        DB_COMMANDER.set_multiple_ingredient_consumption(consumption_names, consumption_amount)
        comment = __build_comment_maker(cocktail)
        DP_CONTROLLER.say_cocktail_ready(comment)

    set_fill_level_bars(w)
    DP_CONTROLLER.reset_alcohol_slider(w)
    shared.cocktail_started = False


def interrupt_cocktail():
    """ Interrupts the cocktail preparation. """
    shared.make_cocktail = False
    print("Canceling Recipe!")
