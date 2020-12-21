# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the maker Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

import sys
import sqlite3
import time
import logging
import re
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from src.bottles import set_fill_level_bars
from src.error_suppression import logerror

from src.database_commander import DatabaseCommander
from src.display_handler import DisplayHandler
from src.rpi_controller import RpiController
from src.display_controller import DisplayController
from src.logger_handler import LoggerHandler
from src.service_handler import ServiceHandler

import globals


database_commander = DatabaseCommander()
display_handler = DisplayHandler()
rpi_controler = RpiController()
display_controller = DisplayController()
service_handler = ServiceHandler()
logger_handler = LoggerHandler("maker_module", "production_logs")


@logerror
def refresh_recipe_maker_view(w, possible_recipes_id=None):
    """ Goes through every recipe in the list or all recipes if none given
    Checks if all ingredients are registered, if so, adds it to the list widget
    """
    if possible_recipes_id is None:
        possible_recipes_id = database_commander.get_enabled_recipes_id()

    available_recipes_ids = []
    bottle_ids = set(database_commander.get_ids_at_bottles())
    handadds_ids = set(database_commander.get_handadd_ids())

    for recipe_id in possible_recipes_id:
        recipe_handadds, recipe_machineadds = database_commander.get_ingredients_seperated_by_handadd(recipe_id)
        recipe_handadds = set(recipe_handadds)
        recipe_machineadds = set(recipe_machineadds)

        if (not recipe_handadds.issubset(handadds_ids)) or (not recipe_machineadds.issubset(bottle_ids)):
            continue

        available_recipes_ids.append(recipe_id)

    recipe_names = database_commander.get_multiple_recipe_names_from_ids(available_recipes_ids)
    display_handler.fill_list_widget(w.LWMaker, recipe_names)


@logerror
def updated_clicked_recipe_maker(w):
    """ Updates the maker display Data with the selected recipe"""
    if not w.LWMaker.selectedItems():
        return

    display_handler.clear_recipe_data_maker(w)
    handle_alcohollevel_change(w)
    cocktailname = w.LWMaker.currentItem().text()

    machineadd_data, handadd_data = database_commander.get_recipe_ingredients_by_name_seperated_data(cocktailname)
    total_volume = sum([v[1] for v in machineadd_data] + [v[1] for v in handadd_data])
    ingredient_data = machineadd_data
    if handadd_data:
        ingredient_data.extend([["", ""], ["Selbst hinzufügen:", ""]])
        ingredient_data.extend(handadd_data)

    display_handler.fill_recipe_data_maker(w, ingredient_data, total_volume, cocktailname)


@logerror
def clear_maker_data(w):
    """ Removes all the Values out of the Maker List. 
    ### will be replaced totally with display_handler.clear_recipe_data_maker(w) in the future, currently just bandaid
    """
    display_handler.clear_recipe_data_maker(w)


def create_recipe_production_properties(ingredient_data, alcohol_faktor, cocktail_volume):
    """Returns the comment and the machinedata if enough ingredients are there"""
    adjusted_data = []
    for ingredient_name, ingredient_volume, ingredient_bottle, ingredient_alcoholic, ingredient_level in ingredient_data:
        factor = alcohol_faktor if ingredient_alcoholic else 1
        adjusted_data.append([ingredient_name, ingredient_volume * factor, ingredient_bottle, ingredient_level])
    total_volume = sum([x[1] for x in adjusted_data])
    volume_factor = cocktail_volume / total_volume
    update_data, volume_list, bottle_list, comment_data, error_data = scale_and_sort_ingredient_data(adjusted_data, volume_factor)
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
                error_data = [ingredient_bottle, ingredient_name, adjusted_volume]
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
    if comment_data:
        comment = "\n\nNoch hinzufügen:"
        for ingredient_name, ingredient_volume in comment_data:
            comment += f"\n- ca. {ingredient_volume:.0f} ml {ingredient_name}"
    return comment


def enough_ingredient(level, needed_volume):
    """Checks if the needed volume is there """
    if needed_volume > level:
        return False
    return True


def generate_maker_log_entry(cocktail_volume, cocktail_name, taken_time, max_time):
    """Enters a log entry for the made cocktail"""
    mengenstring = f"{cocktail_volume} ml"
    if globals.make_cocktail == False:
        pumped_volume = round(cocktail_volume * (taken_time) / max_time)
        abbruchstring = f" - Rezept wurde bei {round(taken_time, 1)} s abgebrochen - {pumped_volume} ml"
    else:
        abbruchstring = ""
    logger_handler.log_event("INFO", f"{mengenstring:8} | {cocktail_name}{abbruchstring}")


def prepare_cocktail(w):
    """ Prepares a Cocktail, if not already another one is in production and enough ingredients are available"""
    if globals.cocktail_started:
        return
    cocktailname, cocktail_volume, alcohol_faktor = display_controller.get_cocktail_data(w)
    if not cocktailname:
        display_handler.standard_box("Kein Rezept ausgewählt!")
        return
    ingredient_data = database_commander.get_recipe_ingredients_with_bottles(cocktailname)
    update_data, ingredient_volumes, ingredient_bottles, comment, error_data = create_recipe_production_properties(
        ingredient_data, alcohol_faktor, cocktail_volume
    )
    if error_data:
        display_handler.standard_box(
            f"Es ist in Flasche {error_data[0]} mit der Zutat {error_data[1]} nicht mehr genug Volumen vorhanden, {error_data[2]:.0f} ml wird benötigt!"
        )
        w.tabWidget.setCurrentIndex(3)
        return

    globals.cocktail_started = True
    globals.make_cocktail = True
    consumption, taken_time, max_time = rpi_controler.make_cocktail(w, ingredient_bottles, ingredient_volumes)
    database_commander.set_recipe_counter(cocktailname)
    generate_maker_log_entry(cocktail_volume, cocktailname, taken_time, max_time)
    print("Verbrauchsmengen: ", consumption)

    service_handler.post_cocktail_to_hook(cocktailname, cocktail_volume)

    if globals.make_cocktail:
        database_commander.set_multiple_ingredient_consumption([x[0] for x in update_data], [x[1] for x in update_data])
        display_handler.standard_box(f"Der Cocktail ist fertig! Bitte kurz warten, falls noch etwas nachtropft.{comment}")
    else:
        consumption_names = [x[0] for x in update_data][: len(consumption)]
        database_commander.set_multiple_ingredient_consumption(consumption_names, consumption)
        display_handler.standard_box("Der Cocktail wurde abgebrochen!")

    set_fill_level_bars(w)
    reset_alcohollevel(w)
    globals.cocktail_started = False


def interrupt_cocktail():
    """ Interrupts the cocktail preparation. """
    globals.make_cocktail = False
    print("Rezept wird abgebrochen!")


@logerror
def reset_alcohollevel(w):
    """ Sets the alcoholintensity to default value (100 %). """
    w.HSIntensity.setValue(0)


@logerror
def handle_alcohollevel_change(w):
    """ Recalculates the alcoholpercentage of the drink with the adjusted Value from the slider. """
    cocktailname, _, alcohol_faktor = display_controller.get_cocktail_data(w)
    if not cocktailname:
        return

    recipe_data = database_commander.get_recipe_ingredients_by_name(cocktailname)
    total_volume = 0
    volume_concentration = 0
    for _, volume, _, concentration in recipe_data:
        factor_volume = 1 if concentration == 0 else alcohol_faktor
        total_volume += volume * factor_volume
        volume_concentration += volume * factor_volume * concentration
    alcohol_level = volume_concentration / total_volume
    display_handler.set_alcohol_level(w, alcohol_level)
