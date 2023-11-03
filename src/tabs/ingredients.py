# -*- coding: utf-8 -*-
""" Module with all necessary functions for the ingredients Tab.
This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from src.tabs import bottles

from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.error_handler import logerror
from src.models import Ingredient


@logerror
def handle_enter_ingredient(w):
    """ Insert or update the ingredient into the DB,
    if all values are given and its name is not already in the DB.
    """
    if not DP_CONTROLLER.validate_ingredient_data(w):
        return
    ingredient = DP_CONTROLLER.get_ingredient_data(w)
    _, _, _, list_widget = DP_CONTROLLER.get_ingredient_fields(w)

    # it's a new ingredient if nothing from the lw is selected
    new_ingredient = not bool(ingredient.selected)

    if new_ingredient:
        successful = _add_new_ingredient(w, ingredient)
    else:
        successful = _change_existing_ingredient(w, list_widget, ingredient)
    if not successful:
        return

    clear_ingredient_information(w)
    DP_CONTROLLER.fill_list_widget(list_widget, [ingredient.name])
    bottles.set_fill_level_bars(w)
    bottles.refresh_bottle_information(w)
    DP_CONTROLLER.say_ingredient_added_or_changed(ingredient.name, new_ingredient, ingredient.selected)


def _add_new_ingredient(w, ing: Ingredient):
    """Adds the ingredient into the database """
    existing_ingredient = DB_COMMANDER.get_ingredient(ing.name)
    if existing_ingredient:
        DP_CONTROLLER.say_name_already_exists()
        return False

    DB_COMMANDER.insert_new_ingredient(
        ing.name, ing.alcohol, ing.bottle_volume, bool(ing.hand), bool(ing.slow), ing.cost
    )
    # needs to fill the ingredient comboboxes, bottles tab only if it is not a handadd
    to_fill = DP_CONTROLLER.get_comboboxes_recipes(w)
    if not ing.hand:
        to_fill.extend(DP_CONTROLLER.get_comboboxes_bottles(w))
    DP_CONTROLLER.fill_multiple_combobox(to_fill, [ing.name])
    return True


def _change_existing_ingredient(w, ingredient_list_widget, ing: Ingredient):
    """Changes the existing ingredient """
    if not ing.selected:
        DP_CONTROLLER.say_no_ingredient_selected()
        return False
    old_ingredient = DB_COMMANDER.get_ingredient(ing.selected)
    if old_ingredient is None:
        raise RuntimeError("This should not be happening. Ingredient not found in DB.")

    bottle_used = DB_COMMANDER.get_bottle_usage(old_ingredient.id)
    # if change to handadd and still used, abort
    if ing.hand and bottle_used:
        DP_CONTROLLER.say_ingredient_still_at_bottle()
        return False

    # in case the volume was lowered below current level get the minimum of both
    volume_level = min(old_ingredient.fill_level, ing.bottle_volume)
    DB_COMMANDER.set_ingredient_data(
        ing.name,
        ing.alcohol,
        ing.bottle_volume,
        volume_level,
        bool(ing.hand),
        bool(ing.slow),
        old_ingredient.id,
        ing.cost,
    )

    DP_CONTROLLER.delete_list_widget_item(ingredient_list_widget, ing.selected)
    combobox_recipes = DP_CONTROLLER.get_comboboxes_recipes(w)
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)

    # Rename in recipes dropdown
    DP_CONTROLLER.rename_multiple_combobox(combobox_recipes, ing.selected, ing.name)

    # add / remove / rename (depending on hand add state change) from bottles dropdown
    # need to do this (and rename), otherwise if changing selected ones, the deletion will change selection
    if old_ingredient.hand and not ing.hand:
        DP_CONTROLLER.fill_multiple_combobox(combobox_bottles, [ing.name])
    elif not old_ingredient.hand and ing.hand:
        DP_CONTROLLER.delete_item_in_multiple_combobox(combobox_bottles, ing.selected)
    else:
        DP_CONTROLLER.rename_multiple_combobox(combobox_bottles, ing.selected, ing.name)

    return True


def load_ingredients(w):
    """ Load all ingredient names into the ListWidget """
    DP_CONTROLLER.clear_list_widget_ingredients(w)
    ingredients = DB_COMMANDER.get_all_ingredients()
    _, _, _, ingredient_list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.fill_list_widget(ingredient_list_widget, [x.name for x in ingredients])


@logerror
def delete_ingredient(w):
    """ Deletes an ingredient out of the DB if its not needed in any recipe."""
    _, _, _, list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    selected_ingredient = DP_CONTROLLER.get_list_widget_selection(list_widget)
    if not selected_ingredient:
        DP_CONTROLLER.say_no_ingredient_selected()
        return
    if not DP_CONTROLLER.ask_to_delete_x(selected_ingredient):
        return
    if not DP_CONTROLLER.password_prompt():
        return

    # Check if still used at a bottle or within a recipe
    ingredient = DB_COMMANDER.get_ingredient(selected_ingredient)
    if not ingredient:
        return
    if DB_COMMANDER.get_bottle_usage(ingredient.id):
        DP_CONTROLLER.say_ingredient_still_at_bottle()
        return
    recipe_list = DB_COMMANDER.get_recipe_usage_list(ingredient.id)
    if recipe_list:
        recipe_string = ", ".join(recipe_list[:10])
        DP_CONTROLLER.say_ingredient_still_at_recipe(recipe_string)
        return

    # if everything is okay, delete from DB and remove from UI
    DB_COMMANDER.delete_ingredient(ingredient.id)
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_bottles(w), ingredient.name)
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_recipes(w), ingredient.name)
    clear_ingredient_information(w)
    load_ingredients(w)
    DP_CONTROLLER.say_ingredient_deleted(ingredient.name)


@logerror
def display_selected_ingredient(w):
    """ Search the DB entry for the ingredient and displays them """
    lineedits, checkbox_hand, checkbox_slow, list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    selected_ingredient = DP_CONTROLLER.get_list_widget_selection(list_widget)
    DP_CONTROLLER.set_ingredient_add_label(w, selected_ingredient != "")
    if selected_ingredient:
        ingredient = DB_COMMANDER.get_ingredient(selected_ingredient)
        if not ingredient:
            return
        DP_CONTROLLER.fill_multiple_lineedit(
            list(lineedits), [ingredient.name, ingredient.alcohol, ingredient.bottle_volume, ingredient.cost]
        )
        DP_CONTROLLER.set_checkbox_value(checkbox_hand, ingredient.hand)
        DP_CONTROLLER.set_checkbox_value(checkbox_slow, ingredient.slow)


@logerror
def clear_ingredient_information(w):
    """ Clears all entries in the ingredient windows. """
    lineedits, checkbox_hand, checkbox_slow, list_widget = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.clean_multiple_lineedit(list(lineedits))
    DP_CONTROLLER.unselect_list_widget_items(list_widget)
    DP_CONTROLLER.set_checkbox_value(checkbox_hand, False)
    DP_CONTROLLER.set_checkbox_value(checkbox_slow, False)
    DP_CONTROLLER.set_ingredient_add_label(w, False)
