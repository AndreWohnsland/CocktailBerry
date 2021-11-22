# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the recipes Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

from collections import Counter

from src.maker import refresh_recipe_maker_view
from src.error_suppression import logerror

from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from config.config_manager import shared


@logerror
def fill_recipe_box_with_ingredients(w):
    """ Asigns all ingredients to the Comboboxes in the recipe tab """
    comboboxes_recipe = DP_CONTROLLER.get_comboboxes_recipes(w)
    ingredient_list = DB_COMMANDER.get_ingredient_names_machine()
    DP_CONTROLLER.fill_multiple_combobox(comboboxes_recipe, ingredient_list, clear_first=True)


def __prepare_enter_new_recipe(recipe_name):
    """Checks if the recipe already exists
    Returns id, got_error"""
    recipe_id = DB_COMMANDER.get_recipe_id_by_name(recipe_name)
    if recipe_id:
        DP_CONTROLLER.say_name_already_exists()
        return recipe_id, True
    return recipe_id, False


def __prepare_update_existing_recipe(w, selected_name):
    """Checks if a recipe is selected and deletes according ingredient data if is valid
    Returns id, got_error"""
    if not selected_name:
        DP_CONTROLLER.say_no_recipe_selected()
        return 0, True
    recipe_id = DB_COMMANDER.get_recipe_id_by_name(selected_name)
    DB_COMMANDER.delete_recipe_ingredient_data(recipe_id)
    DP_CONTROLLER.remove_recipe_from_list_widgets(w, selected_name)
    return recipe_id, False


def __validate_extract_ingredients(ingredient_names, ingredient_volumes):
    """Gives a list for names and volumens of ingredients.
    If some according value is missing, informs the user.
    Returns [names], [volumes], is_valid"""
    names, volumes = [], []
    for name, volume in zip(ingredient_names, ingredient_volumes):
        if (name == "" and volume != "") or (name != "" and volume == ""):
            DP_CONTROLLER.say_some_value_missing()
            return [], [], False
        if name != "":
            names.append(name)
            volumes.append(volume)
    if len(names) == 0:
        DP_CONTROLLER.say_recipe_at_least_one_ingredient()
        return [], [], False
    conter_names = Counter(names)
    double_names = [x[0] for x in conter_names.items() if x[1] > 1]
    if len(double_names) != 0:
        DP_CONTROLLER.say_ingredient_double_usage(double_names[0])
        return [], [], False
    try:
        volumes = [int(x) for x in volumes]
    except ValueError:
        DP_CONTROLLER.say_needs_to_be_int()
        return [], [], False
    return names, volumes, True


def __enter_or_update_recipe(recipe_id, recipe_name, recipe_volume, recipe_alcohollevel, enabled, ingredient_data, comment):
    """Logic to insert/update data into DB"""
    if recipe_id:
        DB_COMMANDER.set_recipe(recipe_id, recipe_name, recipe_alcohollevel, recipe_volume, comment, enabled)
    else:
        DB_COMMANDER.insert_new_recipe(recipe_name, recipe_alcohollevel, recipe_volume, comment, enabled)
        recipe_id = DB_COMMANDER.get_recipe_id_by_name(recipe_name)
    for data in ingredient_data:
        is_alcoholic = 1 if data["alcohollevel"] > 0 else 0
        DB_COMMANDER.insert_recipe_data(recipe_id, data["ID"], data["recipe_volume"], is_alcoholic, 0)
    for hand_id, hand_volume, hand_alcoholic, _, _ in shared.handaddlist:
        DB_COMMANDER.insert_recipe_data(recipe_id, hand_id, hand_volume, hand_alcoholic, 1)
    return recipe_id


@logerror
def enter_recipe(w, newrecipe):
    """ Enters or updates the recipe into the db
    """
    recipe_input = DP_CONTROLLER.get_recipe_field_data(w)
    recipe_name, selected_name, ingredient_names, ingredient_volumes, enabled, comment = recipe_input
    if not recipe_name:
        DP_CONTROLLER.say_enter_cocktailname()
        return
    ingredient_names, ingredient_volumes, is_valid = __validate_extract_ingredients(
        ingredient_names, ingredient_volumes)
    if not is_valid:
        return

    if newrecipe:
        recipe_id, error_message = __prepare_enter_new_recipe(recipe_name)
    else:
        recipe_id, error_message = __prepare_update_existing_recipe(w, selected_name)
    if error_message:
        return

    recipe_volume = sum(ingredient_volumes)
    ingredient_data = []
    recipe_volume_concentration = 0
    for ingredient_name, ingredient_volume in zip(ingredient_names, ingredient_volumes):
        data = DB_COMMANDER.get_ingredient_data(ingredient_name)
        data["recipe_volume"] = ingredient_volume
        recipe_volume_concentration += data["alcohollevel"] * ingredient_volume
        ingredient_data.append(data)
    for _, hand_volume, _, _, hand_alcohollevel in shared.handaddlist:  # id, volume, alcoholic, 1, alcohol_con
        recipe_volume += hand_volume
        recipe_volume_concentration += hand_volume * hand_alcohollevel
    recipe_alcohollevel = int(recipe_volume_concentration / recipe_volume)

    recipe_id = __enter_or_update_recipe(
        recipe_id, recipe_name, recipe_volume, recipe_alcohollevel, enabled, ingredient_data, comment
    )
    DP_CONTROLLER.fill_list_widget_recipes(w, [recipe_name])
    DP_CONTROLLER.clear_recipe_data_maker(w, select_other_item=False)
    if enabled:
        refresh_recipe_maker_view(w, [recipe_id])
    DP_CONTROLLER.clear_recipe_data_recipes(w, False)

    if newrecipe:
        DP_CONTROLLER.say_recipe_added(recipe_name)
    else:
        DP_CONTROLLER.say_recipe_updated(selected_name, recipe_name)


@logerror
def update_recipe_view(w):
    """ Updates the ListWidget in the recipe Tab. """
    recipe_list = DB_COMMANDER.get_recipes_name()
    DP_CONTROLLER.refill_recipes_list_widget(w, recipe_list)


@logerror
def load_selected_recipe_data(w):
    """ Loads all Data from the recipe DB into the according Fields in the recipe tab. """
    _, recipe_name, *_ = DP_CONTROLLER.get_recipe_field_data(w)
    if not recipe_name:
        return

    DP_CONTROLLER.clear_recipe_data_recipes(w, True)
    machineadd_data, _ = DB_COMMANDER.get_recipe_ingredients_by_name_seperated_data(recipe_name)
    ingredient_names = [data[0] for data in machineadd_data]
    ingredient_volumes = [data[1] for data in machineadd_data]
    # This separation is needed here bc above data is only name, volume but for handadd also other parameters are needed
    handadd_data = DB_COMMANDER.get_recipe_ingredients_for_comment(recipe_name)
    enabled = DB_COMMANDER.get_enabled_status(recipe_name)
    DP_CONTROLLER.set_recipe_data(w, recipe_name, ingredient_names, ingredient_volumes, enabled, handadd_data)


@logerror
def delete_recipe(w):
    """ Deletes the selected recipe, requires the Password """
    if not DP_CONTROLLER.check_recipe_password(w):
        DP_CONTROLLER.say_wrong_password()
        return
    _, recipe_name, *_ = DP_CONTROLLER.get_recipe_field_data(w)
    if not recipe_name:
        DP_CONTROLLER.say_no_recipe_selected()
        return

    DB_COMMANDER.delete_recipe(recipe_name)
    DP_CONTROLLER.remove_recipe_from_list_widgets(w, recipe_name)
    DP_CONTROLLER.clear_recipe_data_recipes(w, False)
    DP_CONTROLLER.clear_recipe_data_maker(w)
    DP_CONTROLLER.say_recipe_deleted(recipe_name)


@logerror
def enableall_recipes(w):
    """Set all recipes to enabled """
    disabled_ids = DB_COMMANDER.get_disabled_recipes_id()
    DB_COMMANDER.set_all_recipes_enabled()
    refresh_recipe_maker_view(w, disabled_ids)
    DP_CONTROLLER.clear_recipe_data_recipes(w, True)
    DP_CONTROLLER.say_all_recipes_enabled()
