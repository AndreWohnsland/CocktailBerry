"""Module with all necessary functions for the ingredients Tab.

This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QListWidget

from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER, DatabaseTransactionError
from src.display_controller import DP_CONTROLLER
from src.error_handler import logerror
from src.models import Ingredient
from src.tabs import bottles

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


@logerror
def handle_enter_ingredient(w: MainScreen):
    """Insert or update the ingredient into the DB.

    If all values are given and its name is not already in the DB.
    """
    if not DP_CONTROLLER.validate_ingredient_data(w):
        return
    ingredient = DP_CONTROLLER.get_ingredient_data(w)
    ingredient_input = DP_CONTROLLER.get_ingredient_fields(w)

    # it's a new ingredient if nothing from the lw is selected
    new_ingredient = not bool(ingredient.selected)

    if new_ingredient:
        successful = _add_new_ingredient(w, ingredient)
    else:
        successful = _change_existing_ingredient(w, ingredient_input.selected_ingredient, ingredient)
    if not successful:
        return

    clear_ingredient_information(w)
    DP_CONTROLLER.fill_list_widget(ingredient_input.selected_ingredient, [ingredient.name])
    bottles.set_fill_level_bars(w)
    bottles.refresh_bottle_information(w)
    DP_CONTROLLER.update_maker_view(w)
    DP_CONTROLLER.say_ingredient_added_or_changed(ingredient.name, new_ingredient, ingredient.selected)


def _add_new_ingredient(w: MainScreen, ing: Ingredient) -> bool:
    """Add the ingredient into the database."""
    existing_ingredient = DB_COMMANDER.get_ingredient(ing.name)
    if existing_ingredient:
        DP_CONTROLLER.say_name_already_exists()
        return False

    DB_COMMANDER.insert_new_ingredient(
        ing.name, ing.alcohol, ing.bottle_volume, bool(ing.hand), ing.pump_speed, ing.cost, ing.unit
    )
    # needs to fill the ingredient comboboxes, bottles tab only if it is not a handadd
    to_fill = DP_CONTROLLER.get_comboboxes_recipes(w)
    if not ing.hand:
        to_fill.extend(DP_CONTROLLER.get_comboboxes_bottles(w))
    DP_CONTROLLER.fill_multiple_combobox(to_fill, [ing.name])
    return True


def _change_existing_ingredient(w: MainScreen, ingredient_list_widget: QListWidget, ing: Ingredient) -> bool:
    """Change the existing ingredient."""
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
        ing.pump_speed,
        old_ingredient.id,
        ing.cost,
        ing.unit,
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


def load_ingredients(w: MainScreen):
    """Load all ingredient names into the ListWidget."""
    DP_CONTROLLER.clear_list_widget_ingredients(w)
    ingredients = DB_COMMANDER.get_all_ingredients()
    ingredient_input = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.fill_list_widget(ingredient_input.selected_ingredient, [x.name for x in ingredients])


@logerror
def delete_ingredient(w: MainScreen):
    """Delete an ingredient out of the DB if its not needed in any recipe."""
    ingredient_input = DP_CONTROLLER.get_ingredient_fields(w)
    selected_ingredient = DP_CONTROLLER.get_list_widget_selection(ingredient_input.selected_ingredient)
    if not selected_ingredient:
        DP_CONTROLLER.say_no_ingredient_selected()
        return
    if not DP_CONTROLLER.ask_to_delete_x(selected_ingredient):
        return
    if not DP_CONTROLLER.password_prompt(cfg.UI_MASTERPASSWORD):
        return

    ingredient = DB_COMMANDER.get_ingredient(selected_ingredient)
    if not ingredient:
        return

    # if everything is okay, delete from DB and remove from UI
    try:
        DB_COMMANDER.delete_ingredient(ingredient.id)
    except DatabaseTransactionError as e:
        DP_CONTROLLER.standard_box(str(e), "Error")
        return
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_bottles(w), ingredient.name)
    DP_CONTROLLER.delete_item_in_multiple_combobox(DP_CONTROLLER.get_comboboxes_recipes(w), ingredient.name)
    clear_ingredient_information(w)
    load_ingredients(w)
    DP_CONTROLLER.say_ingredient_deleted(ingredient.name)


@logerror
def display_selected_ingredient(w: MainScreen):
    """Search the DB entry for the ingredient and displays them."""
    ingredient_input = DP_CONTROLLER.get_ingredient_fields(w)
    selected_ingredient = DP_CONTROLLER.get_list_widget_selection(ingredient_input.selected_ingredient)
    DP_CONTROLLER.set_ingredient_add_label(w, selected_ingredient != "")
    if not selected_ingredient:
        return
    ingredient = DB_COMMANDER.get_ingredient(selected_ingredient)
    if not ingredient:
        return
    DP_CONTROLLER.fill_multiple_lineedit(
        [
            ingredient_input.ingredient_name,
            ingredient_input.alcohol_level,
            ingredient_input.volume,
            ingredient_input.ingredient_cost,
            ingredient_input.unit,
            ingredient_input.pump_speed,
        ],
        [
            ingredient.name,
            ingredient.alcohol,
            ingredient.bottle_volume,
            ingredient.cost,
            ingredient.unit,
            ingredient.pump_speed,
        ],
    )
    DP_CONTROLLER.set_checkbox_value(ingredient_input.hand_add, ingredient.hand)


@logerror
def clear_ingredient_information(w: MainScreen):
    """Clear all entries in the ingredient windows."""
    ingredient_input = DP_CONTROLLER.get_ingredient_fields(w)
    DP_CONTROLLER.clean_multiple_lineedit(
        [
            ingredient_input.ingredient_name,
            ingredient_input.alcohol_level,
            ingredient_input.volume,
            ingredient_input.ingredient_cost,
        ]
    )
    DP_CONTROLLER.fill_multiple_lineedit([ingredient_input.unit, ingredient_input.pump_speed], ["ml", "100"])
    DP_CONTROLLER.unselect_list_widget_items(ingredient_input.selected_ingredient)
    DP_CONTROLLER.set_checkbox_value(ingredient_input.hand_add, False)
    DP_CONTROLLER.set_ingredient_add_label(w, False)
