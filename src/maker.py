# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the maker Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

from src.bottles import set_fill_level_bars
from src.error_suppression import logerror

from src.database_commander import DB_COMMANDER
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
    DP_CONTROLLER.fill_list_widget(w.LWMaker, recipe_names)


@logerror
def updated_clicked_recipe_maker(w):
    """ Updates the maker display Data with the selected recipe"""
    if not w.LWMaker.selectedItems():
        return

    DP_CONTROLLER.clear_recipe_data_maker(w)
    handle_alcohollevel_change(w)
    cocktailname = w.LWMaker.currentItem().text()

    machineadd_data, handadd_data = DB_COMMANDER.get_recipe_ingredients_by_name_seperated_data(cocktailname)
    total_volume = sum([v[1] for v in machineadd_data] + [v[1] for v in handadd_data])
    ingredient_data = machineadd_data
    if handadd_data:
        ingredient_data.extend([["", ""], ["HEADER", ""]])
        ingredient_data.extend(handadd_data)

    DP_CONTROLLER.fill_recipe_data_maker(w, ingredient_data, total_volume, cocktailname)


def create_recipe_production_properties(ingredient_data, alcohol_faktor, cocktail_volume):
    """Returns the comment and the machinedata if enough ingredients are there"""
    adjusted_data = []
    for ingredient_name, ingredient_volume, ingredient_bottle, ingredient_alcoholic, ingredient_level in ingredient_data:
        factor = alcohol_faktor if ingredient_alcoholic else 1
        adjusted_data.append([ingredient_name, ingredient_volume * factor, ingredient_bottle, ingredient_level])
    total_volume = sum([x[1] for x in adjusted_data])
    volume_factor = cocktail_volume / total_volume
    update_data, volume_list, bottle_list, comment_data, error_data = scale_and_sort_ingredient_data(
        adjusted_data, volume_factor)
    comment = build_comment_maker(comment_data)
    return update_data, volume_list, bottle_list, comment, error_data


def scale_and_sort_ingredient_data(ingredient_data, volume_factor):
    """Scale all ingrediets by the volume factor, sorts them into bottle and volume"""
    bottle_data = []
    comment_data = []
    bottle_list = []
    volume_list = []
    for ingredient_name, ingredient_volume, ingredient_bottle, ingredient_level in ingredient_data:
        adjusted_volume = round(ingredient_volume * volume_factor)
        if ingredient_bottle:
            if not enough_ingredient(ingredient_level, adjusted_volume):
                error_data = [ingredient_name, ingredient_level, round(adjusted_volume, 0)]
                return [], [], [], "", error_data
            bottle_list.append(ingredient_bottle)
            volume_list.append(adjusted_volume)
            bottle_data.append([ingredient_name, adjusted_volume])
        else:
            comment_data.append([ingredient_name, adjusted_volume])
        update_data = bottle_data + comment_data
    return update_data, volume_list, bottle_list, comment_data, []


def build_comment_maker(comment_data):
    """Build the additional comment for the completion message (if there are handadds)"""
    comment = ""
    for ingredient_name, ingredient_volume in comment_data:
        comment += f"\n- ca. {ingredient_volume:.0f} ml {ingredient_name}"
    return comment


def enough_ingredient(level, needed_volume):
    """Checks if the needed volume is there
    Accepts if there is at least 80% of needed volume
    to be more efficient with the remainder volume in the bottle"""
    if needed_volume * 0.8 > level:
        return False
    return True


def generate_maker_log_entry(cocktail_volume, cocktail_name, taken_time, max_time):
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
    ingredient_data = DB_COMMANDER.get_recipe_ingredients_with_bottles(cocktailname)
    production_props = create_recipe_production_properties(ingredient_data, alcohol_faktor, cocktail_volume)
    update_data, ingredient_volumes, ingredient_bottles, comment, error_data = production_props
    if error_data:
        DP_CONTROLLER.say_not_enough_ingredient_volume(error_data[0], error_data[1], error_data[2])
        w.tabWidget.setCurrentIndex(3)
        return

    print(f"Preparing {cocktail_volume} ml {cocktailname}")
    consumption, taken_time, max_time = RPI_CONTROLLER.make_cocktail(
        w, ingredient_bottles, ingredient_volumes, cocktailname)
    DB_COMMANDER.set_recipe_counter(cocktailname)
    generate_maker_log_entry(cocktail_volume, cocktailname, taken_time, max_time)

    SERVICE_HANDLER.post_cocktail_to_hook(cocktailname, cocktail_volume)
    # only post team if cocktail was made over 60%
    readiness = taken_time / max_time
    if readiness >= 0.6:
        SERVICE_HANDLER.post_team_data(shared.selected_team, round(cocktail_volume * readiness))

    if shared.make_cocktail:
        DB_COMMANDER.set_multiple_ingredient_consumption([x[0] for x in update_data], [x[1] for x in update_data])
        DP_CONTROLLER.say_cocktail_ready(comment)
    else:
        consumption_names = [x[0] for x in update_data][: len(consumption)]
        DB_COMMANDER.set_multiple_ingredient_consumption(consumption_names, consumption)
        DP_CONTROLLER.say_cocktail_canceled()

    set_fill_level_bars(w)
    reset_alcohollevel(w)
    shared.cocktail_started = False


def interrupt_cocktail():
    """ Interrupts the cocktail preparation. """
    shared.make_cocktail = False
    print("Canceling Recipe!")


@logerror
def reset_alcohollevel(w):
    """ Sets the alcoholintensity to default value (100 %). """
    w.HSIntensity.setValue(0)


@logerror
def handle_alcohollevel_change(w):
    """ Recalculates the alcoholpercentage of the drink with the adjusted Value from the slider. """
    cocktailname, _, alcohol_faktor = DP_CONTROLLER.get_cocktail_data(w)
    if not cocktailname:
        return

    recipe_data = DB_COMMANDER.get_recipe_ingredients_by_name(cocktailname)
    total_volume = 0
    volume_concentration = 0
    for _, volume, _, concentration in recipe_data:
        factor_volume = 1 if concentration == 0 else alcohol_faktor
        total_volume += volume * factor_volume
        volume_concentration += volume * factor_volume * concentration
    alcohol_level = volume_concentration / total_volume
    DP_CONTROLLER.set_alcohol_level(w, alcohol_level)
