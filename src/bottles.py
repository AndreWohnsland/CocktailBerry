# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the bottles Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

import sys
import sqlite3
import time
import logging
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *
from collections import Counter

import globals
from src.error_suppression import logerror

from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander
from src.display_controler import DisplayControler
from src.rpi_controller import RpiController
from src.logger_handler import LoggerHandler
from src.supporter import (
    generate_CBB_names,
    generate_LBelegung_names,
    generate_PBneu_names,
    generate_ProBBelegung_names,
)


display_handler = DisplayHandler()
database_commander = DatabaseCommander()
display_controler = DisplayControler()
rpi_controller = RpiController()
logger_handler = LoggerHandler("bottles_module", "production_logs")


def customlevels(w):
    """ Opens the additional window to change the volume levels of the bottles. """
    bot_names = []
    vol_values = []
    w.bottleswindow(bot_names, vol_values)


def get_bottle_ingredients(w):
    """ At the start of the Programm, get all the ingredients from the DB. """
    bottles = database_commander.get_ingredients_at_bottles()
    globals.old_ingredient.extend(bottles)


def refresh_bottle_cb(w):
    """ Adds or remove items to the bottle comboboxes depending on the changed value"""
    # Creating a list of the new and old bottles used
    CBBnames = generate_CBB_names(w)
    old_order = globals.old_ingredient
    new_order = display_controler.get_current_combobox_items(CBBnames)

    new_blist = list(set(new_order) - set(old_order))
    old_blist = list(set(old_order) - set(new_order))
    new_bottle = new_blist[0] if new_blist else ""
    old_bottle = old_blist[0] if old_blist else ""

    display_handler.adjust_bottle_comboboxes(CBBnames, old_bottle, new_bottle)

    register_bottles(w)
    globals.old_ingredient = new_order


@logerror
def newCB_Bottles(w):
    """ Fills each bottle combobox with the possible remaining options
    """
    CBBnames = generate_CBB_names(w)
    used_ingredients = globals.old_ingredient
    possible_ingredients = database_commander.get_ingredient_names_machine()

    shown_ingredients = []
    for row, _ in enumerate(used_ingredients):
        shown_ingredients.append(sorted(set(possible_ingredients) - set([x for i, x in enumerate(used_ingredients) if i != row])))

    display_handler.fill_multiple_combobox_individually(CBBnames, shown_ingredients, True)


@logerror
def register_bottles(w):
    """ Insert the selected Bottleorder into the DB. """
    # this import is neccecary on module level, otherwise there would be a circular import
    from src.maker import refresh_recipe_maker_view

    # Checks where are entries and appends them to a list
    CBBnames = generate_CBB_names(w)
    ingredient_names = display_controler.get_current_combobox_items(CBBnames)
    database_commander.set_bottleorder(ingredient_names)

    refresh_bottle_information(w)
    w.LWMaker.clear()
    refresh_recipe_maker_view(w)
    set_fill_level_bars(w)


@logerror
def read_in_bottles(w):
    """ Reads the Bottleorder into the BottleTab. """
    CBBnames = generate_CBB_names(w)
    ingredient_names = database_commander.get_ingredients_at_bottles()
    display_handler.set_multiple_combobox_items(CBBnames, ingredient_names)


@logerror
def refresh_bottle_information(w):
    """ Loads or updates the Labels of the Bottles (Volumelevel). """
    labels = generate_LBelegung_names(w)
    label_names = database_commander.get_ingredients_at_bottles()
    label_names = [f"  {x}:" if x != "" else "  -  " for x in label_names]
    display_handler.fill_multiple_lineedit(labels, label_names)


@logerror
def renew_checked_bottles(w):
    """ Renews all the Bottles which are checked as new. """
    PBnames = generate_PBneu_names(w)
    renew_bottle = display_controler.get_toggle_status(PBnames)
    database_commander.set_bottle_volumelevel_to_max(renew_bottle)
    display_handler.untoggle_buttons(PBnames)
    set_fill_level_bars(w)
    display_handler.standard_box("Alle Flaschen angewendet!")


@logerror
def set_fill_level_bars(w):
    """ Gets the proportion of actual and maximal volume of each connected bottle and asigns it"""
    progressbars = generate_ProBBelegung_names(w)
    fill_levels = database_commander.get_bottle_fill_levels()
    display_handler.set_progress_bar_values(progressbars, fill_levels)


@logerror
def clean_machine(w):
    """ Activate all Pumps for 20 s to clean them. Needs the Password. Logs the Event. """
    if not display_controler.check_bottles_password(w):
        display_handler.standard_box("Falsches Passwort!!!!")
        return

    display_handler.standard_box("Achtung!: Maschine wird gereinigt, genug Wasser bereitstellen! Ok zum Fortfahren.")
    logger_handler.log_header("INFO", "Cleaning the Pumps")
    rpi_controller.clean_pumps()
    display_handler.standard_box("Fertig!!!")
