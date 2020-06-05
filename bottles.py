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
from msgboxgenerate import standartbox
from loggerconfig import logerror, logfunction

from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander
from src.display_controler import DisplayControler


display_handler = DisplayHandler()
database_commander = DatabaseCommander()
display_controler = DisplayControler()


def generate_cbbnames(w):
    return [getattr(w, f"CBB{x}") for x in range(1, 11)]


def generate_Lnames(w):
    return [getattr(w, f"LBelegung{x}") for x in range(1, 11)]


def customlevels(w, DB, c):
    """ Opens the additional window to change the volume levels of the bottles. """
    bot_names = []
    vol_values = []
    w.bottleswindow(bot_names, vol_values)


def get_bottle_ingredients(w, DB, c):
    """ At the start of the Programm, get all the ingredients from the DB. """
    bottles = database_commander.get_ingredients_at_bottles()
    globals.old_ingredient.extend(bottles)


def refresh_bottle_cb(w, DB, c):
    """ Adds or remove items to the bottle comboboxes depending on the changed value"""
    # Creating a list of the new and old bottles used
    CBBnames = generate_cbbnames(w)
    old_order = globals.old_ingredient
    new_order = display_controler.get_current_combobox_items(CBBnames)

    new_blist = list(set(new_order) - set(old_order))
    old_blist = list(set(old_order) - set(new_order))
    new_bottle = new_blist[0] if new_blist else ""
    old_bottle = old_blist[0] if old_blist else ""

    display_handler.adjust_bottle_comboboxes(CBBnames, old_bottle, new_bottle)

    Belegung_eintragen(w, DB, c)
    globals.old_ingredient = new_order


@logerror
def newCB_Bottles(w, DB, c):
    """ Fills each bottle combobox with the possible remaining options
    """
    CBBnames = generate_cbbnames(w)
    used_ingredients = globals.old_ingredient
    possible_ingredients = database_commander.get_ingredient_names_machine()

    shown_ingredients = []
    for row, _ in enumerate(used_ingredients):
        shown_ingredients.append(
            sorted(set(possible_ingredients) - set([x for i, x in enumerate(used_ingredients) if i != row]))
        )

    display_handler.fill_multiple_combobox_individually(CBBnames, shown_ingredients, True)


@logerror
def Belegung_eintragen(w, DB, c):
    """ Insert the selected Bottleorder into the DB. """
    # this import is neccecary on module level, otherwise there would be a circular import
    from maker import Rezepte_a_M

    # Checks where are entries and appends them to a list
    CBBnames = generate_cbbnames(w)
    ingredient_names = display_controler.get_current_combobox_items(CBBnames)
    database_commander.set_bottleorder(ingredient_names)

    Belegung_a(w, DB, c)
    Rezepte_a_M(w, DB, c)
    Belegung_progressbar(w, DB, c)


@logerror
def Belegung_einlesen(w, DB, c):
    """ Reads the Bottleorder into the BottleTab. """
    CBBnames = generate_cbbnames(w)
    ingredient_names = database_commander.get_ingredients_at_bottles()
    display_handler.set_multiple_combobox_items(CBBnames, ingredient_names)


@logerror
def Belegung_a(w, DB, c):
    """ Loads or updates the Labels of the Bottles (Volumelevel). """
    labels = generate_Lnames(w)
    label_names = database_commander.get_ingredients_at_bottles()
    label_names = [f"  {x}:" if x != "" else "  -  " for x in label_names]
    display_handler.fill_multiple_lineedit(labels, label_names)


@logerror
def Belegung_Flanwenden(w, DB, c):
    """ Renews all the Bottles which are checked as new. """
    PBnames = [getattr(w, f"PBneu{x}") for x in range(1, 11)]
    for Flaschen_C, PBname in enumerate(PBnames):
        if PBname.isChecked():
            c.execute(
                "UPDATE OR IGNORE Zutaten Set Mengenlevel = Flaschenvolumen WHERE ID = (SELECT ID FROM Belegung WHERE Flasche = ?)",
                (Flaschen_C + 1,),
            )
            PBname.setChecked(False)
    DB.commit()
    Belegung_progressbar(w, DB, c)
    standartbox("Alle Flaschen angewendet!")


@logerror
def Belegung_progressbar(w, DB, c):
    """ Gets the actual Level of the Bottle and creates the relation to the maximum Level. \n
    Assigns it to the according ProgressBar.
    """
    for Flaschen_C in range(1, 11):
        storeval = c.execute(
            "SELECT Zutaten.Mengenlevel, Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?",
            (Flaschen_C,),
        ).fetchone()
        ProBname = getattr(w, "ProBBelegung" + str(Flaschen_C))
        if storeval is not None:
            level = storeval[0]
            maximum = storeval[1]
            # Sets the level of the bar, it cant drop below 0 or 100%
            if level <= 0:
                ProBname.setValue(0)
            elif level / maximum > 1:
                ProBname.setValue(100)
            else:
                ProBname.setValue(level / maximum * 100)
        else:
            ProBname.setValue(0)


@logerror
def CleanMachine(w, DB, c, devenvironment):
    """ Activate all Pumps for 20 s to clean them. Needs the Password. Logs the Event. """
    if not devenvironment:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
    if w.LECleanMachine.text() == globals.masterpassword:
        standartbox("Achtung!: Maschine wird gereinigt, genug Wasser bereitstellen! Ok zum Fortfahren.")
        logger = logging.getLogger("cocktail_application")
        template = "{:*^80}"
        logger.info(template.format("Cleaning the Pumps",))
        pin_list = globals.usedpins
        w.LECleanMachine.setText("")
        for row in range(9):
            if not devenvironment:
                GPIO.setup(pin_list[row], GPIO.OUT)
        T_aktuell = 0
        while T_aktuell < 20:
            for row in range(9):
                if not devenvironment:
                    GPIO.output(pin_list[row], 0)
            T_aktuell += 0.1
            T_aktuell = round(T_aktuell, 1)
            time.sleep(0.1)
            qApp.processEvents()
        for row in range(9):
            if not devenvironment:
                GPIO.output(pin_list[row], 1)
        standartbox("Fertig!!!")
    else:
        standartbox("Falsches Passwort!!!!")
    w.LECleanMachine.setText("")
