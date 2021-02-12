# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the bottles Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import globalvars
from src.error_suppression import logerror

from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander
from src.display_controller import DisplayController
from src.rpi_controller import RpiController
from src.logger_handler import LoggerHandler
from src.supporter import (
    generate_CBB_names,
    generate_LBelegung_names,
    generate_PBneu_names,
    generate_ProBBelegung_names,
)


DP_HANDLER = DisplayHandler()
DB_COMMANDER = DatabaseCommander()
DP_CONTROLLER = DisplayController()
RPI_CONTROLLER = RpiController()
LOG_HANDLER = LoggerHandler("bottles_module", "production_logs")


def customlevels(w):
    """ Opens the additional window to change the volume levels of the bottles. """
    bot_names = []
    vol_values = []
    w.bottleswindow(bot_names, vol_values)


def get_bottle_ingredients():
    """ At the start of the Programm, get all the ingredients from the DB. """
    bottles = DB_COMMANDER.get_ingredients_at_bottles()
    globalvars.old_ingredient.extend(bottles)


def refresh_bottle_cb(w):
    """ Adds or remove items to the bottle comboboxes depending on the changed value"""
    # Creating a list of the new and old bottles used
    combobox_bottles = generate_CBB_names(w)
    old_order = globalvars.old_ingredient
    new_order = DP_CONTROLLER.get_current_combobox_items(combobox_bottles)

    new_blist = list(set(new_order) - set(old_order))
    old_blist = list(set(old_order) - set(new_order))
    new_bottle = new_blist[0] if new_blist else ""
    old_bottle = old_blist[0] if old_blist else ""

    DP_HANDLER.adjust_bottle_comboboxes(combobox_bottles, old_bottle, new_bottle)

    register_bottles(w)
    globalvars.old_ingredient = new_order


@logerror
def calculate_combobox_bottles(w):
    """ Fills each bottle combobox with the possible remaining options
    """
    combobox_bottles = generate_CBB_names(w)
    used_ingredients = globalvars.old_ingredient
    possible_ingredients = DB_COMMANDER.get_ingredient_names_machine()

    shown_ingredients = []
    for row, _ in enumerate(used_ingredients):
        shown_ingredients.append(sorted(set(possible_ingredients) - set([x for i, x in enumerate(used_ingredients) if i != row])))

    DP_HANDLER.fill_multiple_combobox_individually(combobox_bottles, shown_ingredients, True)


@logerror
def register_bottles(w):
    """ Insert the selected Bottleorder into the DB. """
    # this import is neccecary on module level, otherwise there would be a circular import
    from src.maker import refresh_recipe_maker_view

    # Checks where are entries and appends them to a list
    combobox_bottles = generate_CBB_names(w)
    ingredient_names = DP_CONTROLLER.get_current_combobox_items(combobox_bottles)
    DB_COMMANDER.set_bottleorder(ingredient_names)

    refresh_bottle_information(w)
    w.LWMaker.clear()
    refresh_recipe_maker_view(w)
    set_fill_level_bars(w)


@logerror
def read_in_bottles(w):
    """ Reads the Bottleorder into the BottleTab. """
    combobox_bottles = generate_CBB_names(w)
    ingredient_names = DB_COMMANDER.get_ingredients_at_bottles()
    DP_HANDLER.set_multiple_combobox_items(combobox_bottles, ingredient_names)


@logerror
def refresh_bottle_information(w):
    """ Loads or updates the Labels of the Bottles (Volumelevel). """
    labels = generate_LBelegung_names(w)
    label_names = DB_COMMANDER.get_ingredients_at_bottles()
    label_names = [f"  {x}:" if x != "" else "  -  " for x in label_names]
    DP_HANDLER.fill_multiple_lineedit(labels, label_names)


@logerror
def renew_checked_bottles(w):
    """ Renews all the Bottles which are checked as new. """
    pushbutton_new_list = generate_PBneu_names(w)
    renew_bottle = DP_CONTROLLER.get_toggle_status(pushbutton_new_list)
    DB_COMMANDER.set_bottle_volumelevel_to_max(renew_bottle)
    DP_HANDLER.untoggle_buttons(pushbutton_new_list)
    set_fill_level_bars(w)
    DP_HANDLER.standard_box("Alle Flaschen angewendet!")


@logerror
def set_fill_level_bars(w):
    """ Gets the proportion of actual and maximal volume of each connected bottle and asigns it"""
    progressbars = generate_ProBBelegung_names(w)
    fill_levels = DB_COMMANDER.get_bottle_fill_levels()
    DP_HANDLER.set_progress_bar_values(progressbars, fill_levels)


@logerror
def clean_machine(w):
    """ Activate all Pumps for 20 s to clean them. Needs the Password. Logs the Event. """
    if not DP_CONTROLLER.check_bottles_password(w):
        DP_HANDLER.standard_box("Falsches Passwort!!!!")
        return

    DP_HANDLER.standard_box("Achtung!: Maschine wird gereinigt, genug Wasser bereitstellen! Ok zum Fortfahren.")
    LOG_HANDLER.log_header("INFO", "Cleaning the Pumps")
    RPI_CONTROLLER.clean_pumps()
    DP_HANDLER.standard_box("Fertig!!!")
