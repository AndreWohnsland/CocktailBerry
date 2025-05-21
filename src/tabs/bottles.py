"""Module with all necessary functions for the bottles Tab.

This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from typing import TYPE_CHECKING

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import shared
from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.error_handler import logerror
from src.machine.controller import MACHINE

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


def get_bottle_ingredients():
    """At the start of the program, get all the ingredients from the DB."""
    bottles = DB_COMMANDER.get_ingredient_names_at_bottles()
    # replace Nones with empty string, command will return none for empty bottles
    shared.old_ingredient = [x if x is not None else "" for x in bottles]


@logerror
def refresh_bottle_cb(w: MainScreen):
    """Add or remove items to the bottle comboboxes depending on the changed value."""
    # Creating a list of the new and old bottles used
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
    old_order = shared.old_ingredient
    new_order = DP_CONTROLLER.get_current_combobox_items(combobox_bottles)

    # subtract the sets of old and new and vice versa to get the changing ingredient
    new_bottle_list = list(set(new_order) - set(old_order))
    old_bottle_list = list(set(old_order) - set(new_order))
    new_bottle = new_bottle_list[0] if new_bottle_list else ""
    old_bottle = old_bottle_list[0] if old_bottle_list else ""

    DP_CONTROLLER.adjust_bottle_comboboxes(combobox_bottles, old_bottle, new_bottle)

    __register_bottles(w)
    shared.old_ingredient = new_order


@logerror
def calculate_combobox_bottles(w: MainScreen):
    """Fill each bottle combobox with the possible remaining options."""
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
    used_ingredients = shared.old_ingredient
    possible_ingredients = DB_COMMANDER.get_all_ingredients(get_hand=False)
    possible_names = [x.name for x in possible_ingredients]

    shown_ingredients = []
    for row, _ in enumerate(used_ingredients):
        used_without_self = {x for i, x in enumerate(used_ingredients) if i != row}
        shown_ingredients.append(sorted(set(possible_names) - used_without_self))

    DP_CONTROLLER.fill_multiple_combobox_individually(combobox_bottles, shown_ingredients, True)


def __register_bottles(w: MainScreen) -> None:
    """Insert the selected bottle order into the DB."""
    # Checks where are entries and appends them to a list
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
    ingredient_names = DP_CONTROLLER.get_current_combobox_items(combobox_bottles)
    DB_COMMANDER.set_bottle_order(ingredient_names)

    refresh_bottle_information(w)
    DP_CONTROLLER.update_maker_view(w)
    set_fill_level_bars(w)


def read_in_bottles(w: MainScreen):
    """Read the bottle_order into the BottleTab."""
    combobox_bottles = DP_CONTROLLER.get_comboboxes_bottles(w)
    ingredient_names = DB_COMMANDER.get_ingredient_names_at_bottles()
    DP_CONTROLLER.set_multiple_combobox_items(combobox_bottles, ingredient_names)


def refresh_bottle_information(w: MainScreen):
    """Load or updates the Labels of the Bottles (volume level)."""
    label_names = DB_COMMANDER.get_ingredient_names_at_bottles()
    label_names = [f"  {x}:" if x else "  -  " for x in label_names]
    DP_CONTROLLER.set_label_bottles(w, label_names)


@logerror
def renew_checked_bottles(w: MainScreen):
    """Renews all the Bottles which are checked as new."""
    pushbutton_new_list = DP_CONTROLLER.get_pushbuttons_newbottle(w)
    renew_bottle = DP_CONTROLLER.get_toggle_status(pushbutton_new_list)
    # build the number of bottles to renew
    bottle_numbers = [x for x, y in enumerate(renew_bottle, 1) if y]
    # if no bottle is selected, skip the process
    if len(bottle_numbers) == 0:
        return
    DP_CONTROLLER.untoggle_buttons(pushbutton_new_list)
    renew_bottles(w, bottle_numbers)


def renew_bottles(w: MainScreen, bottles: list[int]):
    """Renews the bottles at given slot, flush the tubes if needed."""
    DB_COMMANDER.set_bottle_volumelevel_to_max(bottles)
    set_fill_level_bars(w)
    ingredients = []
    # check if any of those slots have a tube volume defined
    for num in bottles:
        ing = DB_COMMANDER.get_ingredient_at_bottle(num)
        if ing is None:
            continue
        pump_config = cfg.PUMP_CONFIG[num - 1]
        if pump_config.tube_volume > 0:
            ing.amount = pump_config.tube_volume
            ingredients.append(ing)
    # if there is at least one tube volume defined, flush the tubes
    if ingredients:
        MACHINE.make_cocktail(w, ingredients, "renew", False)
    DP_CONTROLLER.say_bottles_renewed()


def set_fill_level_bars(w: MainScreen):
    """Get the proportion of actual and maximal volume of each connected bottle and assigns it."""
    progress_bars = DP_CONTROLLER.get_levelbar_bottles(w)
    fill_levels = DB_COMMANDER.get_bottle_fill_levels()
    DP_CONTROLLER.set_progress_bar_values(progress_bars, fill_levels)
