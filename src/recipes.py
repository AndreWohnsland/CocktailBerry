# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the recipes Tab.
This includes all functions for the Lists, DB and Buttos/Dropdowns.
"""

import sys
import sqlite3
import time
import datetime
import csv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *
from collections import Counter

import globals
from src.maker import Rezepte_a_M, Maker_List_null
from src.error_suppression import logerror
from src.supporter import generate_CBR_names

from src.display_handler import DisplayHandler
from src.display_controler import DisplayControler
from src.database_commander import DatabaseCommander

display_handler = DisplayHandler()
display_controler = DisplayControler()
database_commander = DatabaseCommander()


@logerror
def ZutatenCB_Rezepte(w, DB, c):
    """ Asigns all ingredients to the Comboboxes in the recipe tab """
    comboboxes_recipe = generate_CBR_names(w)
    ingredient_list = database_commander.get_ingredient_names_machine()
    display_handler.fill_multiple_combobox(comboboxes_recipe, ingredient_list, clear_first=True)


def prepare_enter_new_recipe(w, recipe_name):
    return ""


def prepare_update_existing_recipe(w, selected_name):
    if not selected_name:
        return "Es ist kein Rezept ausgewählt!"
    return ""


@logerror
def Rezept_eintragen(w, DB, c, newrecipe):
    """ Enters or updates the recipe into the db
    """
    recipe_name, selected_name, ingredient_names, ingredient_volumes, enabled = display_controler.get_recipe_field_data(w)
    if not recipe_name:
        display_handler.standard_box("Bitte Cocktailnamen eingeben!")
        return
    if newrecipe:
        error_message = prepare_enter_new_recipe(w, recipe_name)
    else:
        error_message = prepare_update_existing_recipe(w, selected_name)

    if error_message:
        display_handler.standard_box(error_message)
        return

    neuername = w.LECocktail.text()
    # Checking if both values are given (ingredient and quantity)
    for check_v in range(1, 9):
        CBRname = getattr(w, "CBR" + str(check_v))
        LERname = getattr(w, "LER" + str(check_v))
        if ((CBRname.currentText() != "") and LERname.text() == "") or ((CBRname.currentText() == "") and LERname.text() != ""):
            display_handler.standard_box("Irgendwo ist ein Wert vergessen worden!")
            return
        else:
            # Checks if quantity is a number
            if LERname.text() != "":
                try:
                    int(LERname.text())
                except ValueError:
                    display_handler.standard_box("Menge muss eine Zahl sein!")
                    return
    # Checks, if any ingredient was used twice
    Zutaten_V = []
    Mengen_V = []
    # in addition, also the values are stored into a list for later
    for check_v in range(1, 9):
        CBRname = getattr(w, "CBR" + str(check_v))
        LERname = getattr(w, "LER" + str(check_v))
        if CBRname.currentText() != "":
            Zutaten_V.append(CBRname.currentText())
            Mengen_V.append(int(LERname.text()))
    counted_ing = Counter(Zutaten_V)
    double_ing = [x[0] for x in counted_ing.items() if x[1] > 1]
    if len(double_ing) != 0:
        display_handler.standard_box("Eine der Zutaten:\n<{}>\nwurde doppelt verwendet!".format(double_ing[0]))
        return
    # checks if there is at least one ingredient, else this would make no sense
    if len(Zutaten_V) < 1:
        display_handler.standard_box("Es muss mindestens eine Zutat eingetragen sein!")
        return
    # Checks if the name of the recipe already exists in case of a new recipe
    if newrecipe:
        c.execute("SELECT COUNT(*) FROM Rezepte WHERE Name=?", (neuername,))
        val_check = c.fetchone()[0]
        if not val_check == 0:
            display_handler.standard_box("Dieser Name existiert schon in der Datenbank!")
            return
    # If nothing is wrong, starts writing into DB

    if not newrecipe:
        altername = w.LWRezepte.currentItem().text()
        c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (altername,))
        CocktailID = c.fetchone()[0]
    SVol = 0
    SVolcon = 0
    SVol_alk = 0
    SVolcon_alk = 0
    # Calculates the concentration of the recipe and of the alcoholic/comment part
    for Anzahl in range(0, len(Zutaten_V)):
        c.execute("SELECT Alkoholgehalt FROM Zutaten WHERE Name = ?", (Zutaten_V[Anzahl],))
        Konzentration = c.fetchone()[0]
        Volcon = Mengen_V[Anzahl] * int(Konzentration)
        if Konzentration > 0:
            SVol_alk += Mengen_V[Anzahl]
            SVolcon_alk += Volcon
        SVol += Mengen_V[Anzahl]
        SVolcon += Volcon
    SVol2 = SVol
    c_com = 0
    v_com = 0
    sv_com = 0
    # gets the values of the additional comments
    for row in w.handaddlist:
        v_com += row[1]
        sv_com += row[1] * row[4]
    if sv_com > 0:
        c_com = round(sv_com / v_com, 1)
    SVol2 += v_com
    SVolcon += v_com * c_com
    # Gets the percentage of alcohol the average percentage of pure alcohol and the amount of alcohol
    Alkoholgehalt_Cocktail = int(SVolcon / SVol2)
    if SVol_alk > 0:
        c_alk = int(SVolcon_alk / SVol_alk)
    else:
        c_alk = 0
    v_alk = SVol_alk
    # Checks if the recipe is enabled
    if w.CHBenabled.isChecked():
        isenabled = 1
    else:
        isenabled = 0
    # Insert into recipe DB , deletes old values if its an update
    if newrecipe:
        c.execute(
            "INSERT OR IGNORE INTO Rezepte(Name, Alkoholgehalt, Menge, Kommentar, Anzahl_Lifetime, Anzahl, Enabled, V_Alk, c_Alk, V_Com, c_Com) VALUES (?,?,?,?,0,0,?,?,?,?,?)",
            (neuername, Alkoholgehalt_Cocktail, SVol, w.LEKommentar.text(), isenabled, v_alk, c_alk, v_com, c_com),
        )
    if not newrecipe:
        c.execute(
            "UPDATE OR IGNORE Rezepte SET Name = ?, Alkoholgehalt = ?, Menge = ?, Kommentar = ?, Enabled = ?, V_Alk = ?, c_Alk = ?, V_Com = ?, c_Com = ? WHERE ID = ?",
            (neuername, Alkoholgehalt_Cocktail, SVol, w.LEKommentar.text(), isenabled, v_alk, c_alk, v_com, c_com, int(CocktailID),),
        )
        c.execute("DELETE FROM Zusammen WHERE Rezept_ID = ?", (CocktailID,))
    # RezeptID, Alkoholisch and ZutatenIDs gets inserted into Zusammen DB
    RezepteDBID = c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (neuername,)).fetchone()[0]
    for Anzahl in range(0, len(Zutaten_V)):
        incproperties = c.execute("SELECT ID, Alkoholgehalt FROM Zutaten WHERE Name = ?", (Zutaten_V[Anzahl],)).fetchone()
        ZutatenDBID = incproperties[0]
        if incproperties[1] > 0:
            isalkoholic = 1
        else:
            isalkoholic = 0
        c.execute(
            "INSERT OR IGNORE INTO Zusammen(Rezept_ID, Zutaten_ID, Menge, Alkoholisch, Hand) VALUES (?, ?, ?, ?, 0)",
            (RezepteDBID, ZutatenDBID, Mengen_V[Anzahl], isalkoholic),
        )
    # Insert all the handadds to the db on its seperate rows
    for row in w.handaddlist:
        c.execute(
            "INSERT OR IGNORE INTO Zusammen(Rezept_ID, Zutaten_ID, Menge, Alkoholisch, Hand) VALUES (?, ?, ?, ?, 1)",
            (RezepteDBID, row[0], row[1], row[2]),
        )
    DB.commit()
    # Removing the old name from the list and adds the new one, clears the fields
    if not newrecipe:
        delfind = w.LWRezepte.findItems(altername, Qt.MatchExactly)
        if len(delfind) > 0:
            for item in delfind:
                w.LWRezepte.takeItem(w.LWRezepte.row(item))
        delfind = w.LWMaker.findItems(altername, Qt.MatchExactly)
        if len(delfind) > 0:
            for item in delfind:
                w.LWMaker.takeItem(w.LWMaker.row(item))
    w.LWRezepte.addItem(neuername)
    # add needs to be checked, if all ingredients are used
    if isenabled:
        Rezepte_a_M(w, DB, c, [RezepteDBID])
    display_handler.clear_recipe_data_recipes(w, False)
    if newrecipe:
        display_handler.standard_box("Rezept unter der ID und dem Namen:\n<{}> <{}>\neingetragen!".format(RezepteDBID, neuername))
    else:
        display_handler.standard_box(
            "Rezept mit der ID und dem Namen:\n<{}> <{}>\nunter dem Namen:\n<{}>\naktualisiert!".format(RezepteDBID, altername, neuername)
        )


@logerror
def Rezepte_a_R(w, DB, c):
    """ Updates the ListWidget in the recipe Tab. """
    recipe_list = database_commander.get_recipes_name()
    display_handler.refill_recipes_list_widget(w, recipe_list)


@logerror
def Rezepte_clear(w, DB, c, select_other_item):
    """ will be removed with the ui refactoring """
    display_handler.clear_recipe_data_recipes(w, select_other_item)


@logerror
def Rezepte_Rezepte_click(w, DB, c):
    """ Loads all Data from the recipe DB into the according Fields in the recipe tab. """
    recipe_name = display_controler.get_list_widget_selection(w.LWRezepte)
    if not recipe_name:
        return

    display_handler.clear_recipe_data_recipes(w, True)
    machineadd_data, _ = database_commander.get_recipe_ingredients_by_name_seperated_data(recipe_name)
    ingredient_names = [data[0] for data in machineadd_data]
    ingredient_volumes = [data[1] for data in machineadd_data]
    handadd_data = database_commander.get_recipe_ingredients_for_comment(recipe_name)
    enabled = database_commander.get_enabled_status(recipe_name)
    display_handler.set_recipe_data(w, recipe_name, ingredient_names, ingredient_volumes, enabled, handadd_data)


@logerror
def Rezepte_delete(w, DB, c):
    """ Deletes the selected recipe, requires the Password """
    if not display_controler.check_recipe_password(w):
        display_handler.standard_box("Falsches Passwort!")
        return
    recipe_name = display_controler.get_list_widget_selection(w.LWRezepte)
    if not recipe_name:
        display_handler.standard_box("Kein Rezept ausgewählt!")
        return

    database_commander.delete_recipe(recipe_name)
    display_handler.remove_recipe_from_list_widgets(w, recipe_name)
    display_handler.clear_recipe_data_recipes(w, False)
    display_handler.clear_recipe_data_maker(w)
    display_handler.standard_box(f"Rezept mit dem Namen <{recipe_name}> wurde gelöscht!")


@logerror
def enableall(w, DB, c):
    """Set all recipes to enabled """
    disabled_ids = database_commander.get_disabled_recipes_id()
    database_commander.set_all_recipes_enabled()
    Rezepte_a_M(w, DB, c, disabled_ids)
    display_handler.clear_recipe_data_recipes(w, True)
    display_handler.standard_box("Alle Rezepte wurden wieder aktiv gesetzt!")
