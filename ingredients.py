# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the ingredients Tab.
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

from recipes import ZutatenCB_Rezepte
from bottles import Belegung_progressbar, Belegung_a
from msgboxgenerate import standartbox
from loggerconfig import logfunction, logerror

from src.display_controler import DisplayControler
from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander

from src.supporter import generate_ingredient_fields, generate_CBB_names, generate_CBR_names

import globals

display_controler = DisplayControler()
display_handler = DisplayHandler()
database_commander = DatabaseCommander()


def custom_output(w, DB, c):
    w.ingredientdialog()


@logerror
def Zutat_eintragen(w, DB, c, newingredient=True):
    """ Insert the new ingredient into the DB, if all values are given 
    and its name is not already in the DB.
    Also can change the current selected ingredient (newingredient = False)
    """
    ingredient_lineedits, ingredient_checkbox, ingredient_list_widget = generate_ingredient_fields(w)
    error = display_controler.check_ingredient_data(ingredient_lineedits)
    if error:
        display_handler.standard_box(error[0])
        return
    ingredient_data = display_controler.get_ingredient_data(ingredient_lineedits, ingredient_checkbox, ingredient_list_widget)

    if newingredient:
        succesfull = add_new_ingredient(w, ingredient_data)
    else:
        succesfull = change_existing_ingredient(w, ingredient_list_widget, ingredient_data)
    if not succesfull:
        return

    Zutaten_clear(w, DB, c)
    ingredient_list_widget.addItem(ingredient_data["ingredient_name"])
    Belegung_progressbar(w, DB, c)
    Belegung_a(w, DB, c)
    display_handler.standard_box(succesfull)


def add_new_ingredient(w, ingredient_data):
    combobox_recipes = generate_CBR_names(w)
    combobox_bottles = generate_CBB_names(w)
    given_name_ingredient_data = database_commander.get_ingredient_data(ingredient_data["ingredient_name"])
    if given_name_ingredient_data:
        display_handler.standard_box("Dieser Name existiert schon in der Datenbank!")
        return ""

    database_commander.insert_new_ingredient(
        ingredient_data["ingredient_name"], ingredient_data["alcohollevel"], ingredient_data["volume"], ingredient_data["hand_add"]
    )
    if not ingredient_data["hand_add"]:
        display_handler.fill_multiple_combobox(combobox_recipes, [ingredient_data["ingredient_name"]])
        display_handler.fill_multiple_combobox(combobox_bottles, [ingredient_data["ingredient_name"]])
    return f"Zutat mit dem Namen: <{ingredient_data['ingredient_name']}> eingetragen"


def change_existing_ingredient(w, ingredient_list_widget, ingredient_data):
    combobox_recipes = generate_CBR_names(w)
    combobox_bottles = generate_CBB_names(w)
    selected_ingredient_data = database_commander.get_ingredient_data(ingredient_data["selected_ingredient"])
    if not ingredient_data["selected_ingredient"]:
        display_handler.standard_box("Es ist keine Zutat ausgewählt!")
        return ""

    bottle_used = database_commander.get_bottle_usage(selected_ingredient_data["ID"])
    if ingredient_data["hand_add"] and bottle_used:
        display_handler.standard_box(
            "Die Zutat ist noch in der Belegung registriert und kann somit nicht auf selbst hinzufügen gesetzt werden!"
        )
        return ""

    volume_level = min(selected_ingredient_data["volume_level"], ingredient_data["volume"])
    database_commander.set_ingredient_data(
        ingredient_data["ingredient_name"],
        ingredient_data["alcohollevel"],
        ingredient_data["volume"],
        volume_level,
        ingredient_data["hand_add"],
        selected_ingredient_data["ID"],
    )

    display_handler.delete_list_widget_item(ingredient_list_widget, ingredient_data["selected_ingredient"])

    if selected_ingredient_data["hand_add"] and not ingredient_data["hand_add"]:
        display_handler.fill_multiple_combobox(combobox_recipes, [ingredient_data["ingredient_name"]])
        display_handler.fill_multiple_combobox(combobox_bottles, [ingredient_data["ingredient_name"]])
    elif not ingredient_data["hand_add"]:
        display_handler.rename_multiple_combobox(
            combobox_recipes, ingredient_data["selected_ingredient"], ingredient_data["ingredient_name"]
        )
        display_handler.rename_multiple_combobox(
            combobox_bottles, ingredient_data["selected_ingredient"], ingredient_data["ingredient_name"]
        )
    else:
        display_handler.delete_item_in_multiple_combobox(combobox_recipes, ingredient_data["selected_ingredient"])
        display_handler.delete_item_in_multiple_combobox(combobox_bottles, ingredient_data["selected_ingredient"])

    return f"Zutat mit dem Namen: <{ingredient_data['selected_ingredient']}> unter <{ingredient_data['ingredient_name']}> aktualisiert"


@logerror
def Zutaten_a(w, DB, c):
    """ Load all ingredientnames into the ListWidget """
    w.LWZutaten.clear()
    cursor_buffer = c.execute("SELECT Name FROM Zutaten")
    for values in cursor_buffer:
        w.LWZutaten.addItem(values[0])


@logerror
def Zutaten_delete(w, DB, c):
    """ Deletes an ingredient out of the DB if its not needed in any recipe. \n
    In addition to do so, a password is needed in the interface.
    """
    ZID = 0
    if w.LEpw2.text() == globals.MASTERPASSWORD:
        if not w.LWZutaten.selectedItems():
            standartbox("Keine Zutat ausgewählt!")
        else:
            Zname = w.LWZutaten.currentItem().text()
            cursor_buffer = c.execute("SELECT ID FROM Zutaten WHERE Name = ?", (Zname,))
            for row in cursor_buffer:
                ZID = row[0]
            c.execute("SELECT COUNT(*) FROM Zusammen WHERE Zutaten_ID=?", (ZID,))
            Zutatentest = c.fetchone()[0]
            # Checks if the ingredient is used in any bottle or in any recipe and reacts accordingly
            if Zutatentest == 0:
                c.execute("SELECT COUNT(*) FROM Belegung WHERE ID=?", (ZID,))
                Zutatentest = c.fetchone()[0]
                if Zutatentest == 0:
                    c.execute("DELETE FROM Zutaten WHERE ID = ?", (ZID,))
                    DB.commit()
                    # For optimisation this command here can be switched with a simpe remove for the ingredient
                    ZutatenCB_Rezepte(w, DB, c)
                    # Find the ingredient ind the Comboboxes for the Bottles and removes it
                    for box in range(1, 11):
                        CBBname = getattr(w, "CBB" + str(box))
                        index = CBBname.findText(Zname, Qt.MatchFixedString)
                        if index >= 0:
                            CBBname.removeItem(index)
                    Zutaten_clear(w, DB, c)
                    Zutaten_a(w, DB, c)
                    standartbox("Zutat mit der ID und dem Namen:\n<{}> <{}>\ngelöscht!".format(ZID, Zname))
                else:
                    standartbox("Achtung, die Zutat ist noch in der Belegung registriert!")
            # if the ingredient is still used in recipes, inform the user about it and the first 10 recipes
            else:
                stringsaver = c.execute(
                    "SELECT Rezepte.Name FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID = Zusammen.Rezept_ID WHERE Zusammen.Zutaten_ID=?",
                    (ZID,),
                )
                Zutatenliste = []
                for output in stringsaver:
                    Zutatenliste.append(output[0])
                    if len(Zutatenliste) >= 10:
                        break
                Zutatenstring = ", ".join(Zutatenliste)
                standartbox(
                    "Zutat kann nicht gelöscht werden, da sie in {} Rezept(en) genutzt wird! Diese sind (maximal die zehn ersten):\n{}".format(
                        Zutatentest, Zutatenstring
                    )
                )
    else:
        standartbox("Falsches Passwort!")
    w.LEpw2.setText("")


@logerror
def Zutaten_Zutaten_click(w, DB, c):
    """ Search the DB entry for the ingredient and displays them """
    if w.LWZutaten.selectedItems():
        ingredientname = w.LWZutaten.currentItem().text()
        cursor_buffer = c.execute("SELECT Alkoholgehalt, Flaschenvolumen, Hand FROM Zutaten WHERE Name = ?", (ingredientname,))
        for row in cursor_buffer:
            w.LEGehaltRezept.setText(str(row[0]))
            w.LEFlaschenvolumen.setText(str(row[1]))
            if row[2] == 1:
                w.CHBHand.setChecked(True)
            else:
                w.CHBHand.setChecked(False)
        w.LEZutatRezept.setText(ingredientname)


@logerror
def Zutaten_clear(w, DB, c):
    """ Clears all entries in the ingredient windows. """
    w.LWZutaten.clearSelection()
    w.LEZutatRezept.clear()
    w.LEGehaltRezept.clear()
    w.LEFlaschenvolumen.clear()
    w.CHBHand.setChecked(False)
