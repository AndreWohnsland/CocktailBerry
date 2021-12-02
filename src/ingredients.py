# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the ingredients Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""
from src.bottles import set_fill_level_bars, refresh_bottle_information

from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER


def enter_ingredient(w, newingredient=True):
    """ Insert the new ingredient into the DB, if all values are given and its name is not already in the DB.
    Also can change the current selected ingredient (newingredient = False)
    """
    ingredient_lineedits, ingredient_checkbox, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    valid_data = DP_CONTROLLER.validate_ingredient_data(ingredient_lineedits)
    if not valid_data:
        return
    ingredient_data = DP_CONTROLLER.get_ingredient_data(
        ingredient_lineedits, ingredient_checkbox, ingredient_list_widget)

    if newingredient:
        succesfull = __add_new_ingredient(w, ingredient_data)
    else:
        succesfull = __change_existing_ingredient(w, ingredient_list_widget, ingredient_data)
    if not succesfull:
        return

    clear_ingredient_information(w)
    DP_CONTROLLER.fill_list_widget(ingredient_list_widget, [ingredient_data["ingredient_name"]])
    set_fill_level_bars(w)
    refresh_bottle_information(w)
    DP_CONTROLLER.say_ingredient_added_or_changed(
        ingredient_data["ingredient_name"],
        newingredient,
        ingredient_data["selected_ingredient"]
    )


def __add_new_ingredient(w, ingredient_data):
    """Adds the ingredient into the database """
    existing_ingredient = DB_COMMANDER.get_ingredient(ingredient_data["ingredient_name"])
    if existing_ingredient:
        DP_CONTROLLER.say_name_already_exists()
        return False

    DB_COMMANDER.insert_new_ingredient(
        ingredient_data["ingredient_name"],
        ingredient_data["alcohollevel"],
        ingredient_data["volume"],
        ingredient_data["hand_add"]
    )
    if not ingredient_data["hand_add"]:
        combobox_recipes = DP_CONTROLLER.get_comboboxes_recipes(w)
        combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
        DP_CONTROLLER.fill_multiple_combobox(combobox_recipes + combobox_bottles, [ingredient_data["ingredient_name"]])
    return True


def __change_existing_ingredient(w, ingredient_list_widget, ingredient_data):
    """Changes the existing ingredient """
    if not ingredient_data["selected_ingredient"]:
        DP_CONTROLLER.say_no_ingredient_selected()
        return False
    old_ingredient = DB_COMMANDER.get_ingredient(ingredient_data["selected_ingredient"])

    bottle_used = DB_COMMANDER.get_bottle_usage(old_ingredient.id)
    # if change to handadd and still used, abort
    if ingredient_data["hand_add"] and bottle_used:
        DP_CONTROLLER.say_ingredient_still_at_bottle()
        return False

    # in case the volume was lowered below current level get the minimum of both
    volume_level = min(old_ingredient.fill_level, ingredient_data["volume"])
    DB_COMMANDER.set_ingredient_data(
        ingredient_data["ingredient_name"],
        ingredient_data["alcohollevel"],
        ingredient_data["volume"],
        volume_level,
        ingredient_data["hand_add"],
        old_ingredient.id,
    )

    DP_CONTROLLER.delete_list_widget_item(ingredient_list_widget, ingredient_data["selected_ingredient"])
    combobox_recipes = DP_CONTROLLER.get_comboboxes_recipes(w)
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
    both_boxes = combobox_recipes + combobox_bottles

    if old_ingredient.hand and not ingredient_data["hand_add"]:
        DP_CONTROLLER.fill_multiple_combobox(both_boxes, [ingredient_data["ingredient_name"]])
    elif not ingredient_data["hand_add"]:
        DP_CONTROLLER.rename_multiple_combobox(
            both_boxes,
            ingredient_data["selected_ingredient"],
            ingredient_data["ingredient_name"]
        )
    else:
        DP_CONTROLLER.delete_item_in_multiple_combobox(both_boxes, ingredient_data["selected_ingredient"])

    return True


def load_ingredients(w):
    """ Load all ingredientnames into the ListWidget """
    DP_CONTROLLER.clear_list_widget_ingredients(w)
    ingredient_names = DB_COMMANDER.get_ingredient_names()
    _, _, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.fill_list_widget(ingredient_list_widget, ingredient_names)


def delete_ingredient(w):
    """ Deletes an ingredient out of the DB if its not needed in any recipe."""
    _, _, list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    if not DP_CONTROLLER.check_ingredient_password(w):
        DP_CONTROLLER.say_wrong_password()
        return
    selected_ingredient = DP_CONTROLLER.get_list_widget_selection(list_widget)
    if not selected_ingredient:
        DP_CONTROLLER.say_no_ingredient_selected()
        return
    ingredient = DB_COMMANDER.get_ingredient(selected_ingredient)
    if DB_COMMANDER.get_bottle_usage(ingredient.id):
        DP_CONTROLLER.say_ingredient_still_at_bottle()
        return
    recipe_list = DB_COMMANDER.get_recipe_usage_list(ingredient.id)
    if recipe_list:
        recipe_string = ", ".join(recipe_list[:10])
        DP_CONTROLLER.say_ingredient_still_at_recipe(recipe_string)
        return

    DB_COMMANDER.delete_ingredient(ingredient.id)
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_bottles(w), ingredient.name)
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_recipes(w), ingredient.name)
    clear_ingredient_information(w)
    load_ingredients(w)
    DP_CONTROLLER.say_ingredient_deleted(ingredient.name)


def display_selected_ingredient(w):
    """ Search the DB entry for the ingredient and displays them """
    lineedits, checkbox, list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    selected_ingredient = DP_CONTROLLER.get_list_widget_selection(list_widget)
    if selected_ingredient:
        ingredient = DB_COMMANDER.get_ingredient(selected_ingredient)
        DP_CONTROLLER.fill_multiple_lineedit(
            lineedits, [ingredient.name, ingredient.alcohol, ingredient.bottle_volume]
        )
        DP_CONTROLLER.set_checkbox_value(checkbox, ingredient.hand)


def clear_ingredient_information(w):
    """ Clears all entries in the ingredient windows. """
    lineedits, checkbox, list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.clean_multiple_lineedit(lineedits)
    DP_CONTROLLER.unselect_list_widget_items(list_widget)
    DP_CONTROLLER.set_checkbox_value(checkbox, False)
