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

from bottles import Belegung_progressbar
from msgboxgenerate import standartbox
from loggerconfig import logfunction, logerror

import globals


@logerror
def Rezepte_a_M(w, DB, c, reloadall=True, mode="", changeid=0, goon=True):
    """ Goes through every recipe in the DB and crosscheck its ingredients 
    with the actual bottle assignments. \n
    Only display the recipes in the maker tab which match all bottles needed.
    In addition, only shows enabled recipes.
    By default, clears the Widget and load all DB entries new.
    The mode is add or enable for the recipes or empty if none of them.
    changeid is only needed for add (int) and enable (list).
    goon is only needed at recipes and represents if the new/updated recipe is disabled or not
    """
    if reloadall:
        w.LWMaker.clear()
    possible_recipes_id = []
    available_recipes_ids = []
    # Search all ids needed, depending on the mode
    # this differs on the input: changed bottles, add an recipe (or changed) or enabled/disabled a recipe
    if mode == "add":
        possible_recipes_id.append(changeid)
    elif mode == "enable":
        possible_recipes_id = changeid
    else:
        cursor_buffer = c.execute("SELECT ID, Enabled FROM Rezepte")
        for values in cursor_buffer:
            if values[1]:
                possible_recipes_id.append(int(values[0]))
    # Search all ingredient IDs of the recipe
    # if its only one recipe change and it is not enabled, this part will not be carried out
    if not goon:
        return

    for recipe_id in possible_recipes_id:
        can_do_recipe = True
        # Generates a list of all Ids of the ingredients needed by the machine for every recipe
        ingredient_ids_machine = []
        cursor_buffer = c.execute("SELECT Zutaten_ID FROM Zusammen WHERE Rezept_ID = ? AND Hand=0", (recipe_id,))
        for values in cursor_buffer:
            ingredient_ids_machine.append(int(values[0]))
        # Check if all Bottles for the Recipe are Connected, if so adds it to the List
        for ingredient_id in ingredient_ids_machine:
            c.execute("SELECT COUNT(*) FROM Belegung WHERE ID = ?", (ingredient_id,))
            cursor_buffer2 = c.fetchone()[0]
            if cursor_buffer2 == 0:
                can_do_recipe = False
                break
        # Generates a list of all Ids of the ingredients which needs to be added later by hand
        ingredient_ids_hand = []
        cursor_buffer = c.execute("SELECT Zutaten_ID FROM Zusammen WHERE Rezept_ID = ? AND Hand=1", (recipe_id,))
        for values in cursor_buffer:
            ingredient_ids_hand.append(int(values[0]))
        # Check if all ingredients for the Recipe are set available (Vorhanden DB got the list), if so adds it to the List
        for ingredient_id in ingredient_ids_hand:
            c.execute("SELECT COUNT(*) FROM Vorhanden WHERE ID = ?", (ingredient_id,))
            cursor_buffer2 = c.fetchone()[0]
            if cursor_buffer2 == 0:
                can_do_recipe = False
                break
        if can_do_recipe:
            available_recipes_ids.append(recipe_id)
    # alle möglichen Rezepte werden über ihre ID in Liste eingetragen
    for recipe_id in available_recipes_ids:
        name_ = c.execute("SELECT Name FROM Rezepte WHERE ID = ?", (recipe_id,)).fetchone()[0]
        w.LWMaker.addItem(name_)


@logerror
def Maker_Rezepte_click(w, DB, c):
    """ Get all the data out of the DB for the selected recipe,
    then assign the strings and values in the TextBoxes on the Maker Sheet.
    """
    if w.LWMaker.selectedItems():
        # search the DB for the recipe (ID) over the ID (Zutaten) fetch the ingredients and amount
        Maker_List_null(w, DB, c)
        zusatzmenge = 0
        # gets the alcohol percentage
        Maker_ProB_change(w, DB, c)
        # Gets and sets the name
        cocktailname = w.LWMaker.currentItem().text()
        w.LAlkoholname.setText(cocktailname)
        # First gets all the ingredients added by the machine
        cursor_buffer = c.execute(
            "SELECT Zutaten.Name, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ? AND Zusammen.Hand=0",
            (cocktailname,),
        )
        ingredient_names = []
        ingredient_volume = []
        # assigns the values to the boxes
        for ingredientdata in cursor_buffer:
            ingredient_names.append(ingredientdata[0])
            ingredient_volume.append(ingredientdata[1])
        # generates the additional incredients to add. Therefore fills in a blank line and afterwards a header
        # If there are no additional adds, just skip that part
        cursor_buffer = c.execute(
            "SELECT Z.Zutaten_ID, Z.Menge FROM Zusammen AS Z INNER JOIN Rezepte AS R ON R.ID=Z.Rezept_ID WHERE R.Name = ? AND Z.Hand=1",
            (cocktailname,),
        )
        commentlist = [row for row in cursor_buffer]
        # if there are any additional ingredients generate the additional entries in the list
        if len(commentlist) > 0:
            ingredient_names.extend(["", "Selbst hinzufügen:"])
            ingredient_volume.extend(["", ""])
            for commentdata in commentlist:
                handname = c.execute("SELECT Name FROM Zutaten WHERE ID=?", (commentdata[0],)).fetchone()[0]
                ingredient_names.append(handname)
                ingredient_volume.append(commentdata[1])
                zusatzmenge += commentdata[1]
        # Adds up both the machine and manual add volume for the total volume
        cursor_buffer = c.execute("SELECT Menge FROM Rezepte WHERE Name = ?", (cocktailname,)).fetchone()[0]
        w.LMenge.setText(f"Menge: {int(cursor_buffer) + zusatzmenge} ml")
        # loops through the list and give the string to the labels, also give the "Hinzufügen" another color for better visualibility
        for row, (name_, volume) in enumerate(zip(ingredient_names, ingredient_volume), 1):
            LZname = getattr(w, f"LZutat{row}")
            LZname.setText(f"{name_} ")
            LMZname = getattr(w, f"LMZutat{row}")
            if volume != "":
                LMZname.setText(f" {volume} ml")
            if name_ == "Selbst hinzufügen:":
                LZname.setStyleSheet("color: rgb(170, 170, 170)")


@logerror
def Maker_List_null(w, DB, c):
    """ Removes all the Values out of the Maker List. """
    w.LAlkoholgehalt.setText("")
    w.LAlkoholname.setText("")
    w.LMenge.setText("")
    for check_v in range(1, 11):
        LZname = getattr(w, f"LZutat{check_v}")
        LZname.setText("")
        LMZname = getattr(w, f"LMZutat{check_v}")
        LMZname.setText("")
        LZname.setStyleSheet("color: rgb(0, 123, 255)")


@logfunction
def Maker_Zubereiten(w, DB, c, devenvironment):
    """ Starts the Cocktail Making procedure, if not already started.\n
    ------------------------------------------------------------ 
    The global variable "loopcheck" is to interrupt the procedure over the cancel button
    and the belonging function for this button. \n
    ------------------------------------------------------------
    In this Function, the Pins and the Volumeflow of each connected Pump are defined,
    if anything changes, it needs to be adapted here/in the global.py.
    """
    if not devenvironment:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
    # can only start one process
    if globals.startcheck == True:
        return
    if not w.LWMaker.selectedItems():
        standartbox("Kein Rezept ausgewählt!")
        return

    ingredient_amount = []
    bottle_number = []
    pump_times = []
    pump_volume_flows = []
    used_pins = []
    consumption_ingredients = []

    globals.startcheck = True
    calculated_volume = 0
    timestep = 0.05
    cocktail_volume = int(w.LCustomMenge.text())
    alcohol_faktor = 1 + (w.HSIntensity.value() / 100)

    globals.loopcheck = True
    pin_list = globals.USEDPINS
    volume_flows = globals.PUMP_VOLUMEFLOW

    # gets the ID and the amount for the recipe
    cocktailname = w.LWMaker.currentItem().text()
    cursor_buffer = c.execute("SELECT ID, Menge FROM Rezepte WHERE Name = ?", (cocktailname,)).fetchone()
    CocktailID = cursor_buffer[0]
    # gets all the amounts, Bottles and alctype for the recipe
    cursor_buffer = c.execute(
        "SELECT Zusammen.Menge, Belegung.Flasche, Zusammen.Alkoholisch From Zusammen INNER JOIN Belegung ON Zusammen.Zutaten_ID = Belegung.ID WHERE Zusammen.Rezept_ID = ? AND Zusammen.Hand=0",
        (CocktailID,),
    )

    for amount, bottle, alcoholic in cursor_buffer:
        # if the ingredient is alcoholic assign the factor
        alcohol_multiplier = alcohol_faktor if alcoholic == 1 else 1
        # creates the list for amount, bottlenumber, time, volume and consumption for each ingredient
        ingredient_amount.append(round(int(amount) * alcohol_multiplier, 1))
        bottle_number.append(int(bottle))
        pump_volume_flows.append(volume_flows[int(bottle) - 1])
        used_pins.append(pin_list[int(bottle) - 1])
        pump_times.append(round((int(amount) * alcohol_multiplier) / volume_flows[int(bottle) - 1], 2))
        calculated_volume += round(int(amount) * alcohol_multiplier, 1)
        consumption_ingredients.append(0)
    # If there is a comment, it will be checked, and the quantity of the ingredients will be added to the calculated_volume
    # gets all values from the DB which needed to be added via hand later
    cursor_buffer = c.execute(
        "SELECT Zutaten.Name, Z.Menge, Z.Alkoholisch, Zutaten.ID FROM Zusammen AS Z INNER JOIN Rezepte AS R ON R.ID=Z.Rezept_ID INNER JOIN Zutaten ON Z.Zutaten_ID=Zutaten.ID WHERE R.ID = ? AND Z.Hand=1",
        (CocktailID,),
    )
    commentlist = [row for row in cursor_buffer]
    zusatzstring = ""
    hand_consumption = []
    for _, amount, alcoholic, incredient_id in commentlist:
        alcohol_multiplier = alcohol_faktor if alcoholic == 1 else 1
        hand_volume = round(int(amount) * alcohol_multiplier, 1)
        hand_consumption.append([incredient_id, hand_volume])
        calculated_volume += hand_volume
    # Checks it the calculated volume is the desired volume, due to concentrating factors and comments, this can vary
    # Calculates the difference and then adjust all values and the times
    volume_multiplier = cocktail_volume / calculated_volume
    for x in range(len(ingredient_amount)):
        ingredient_amount[x] = round(ingredient_amount[x] * volume_multiplier, 1)
        pump_times[x] = round(pump_times[x] * volume_multiplier, 1)
    # Checks if there is still enough volume in the Bottle
    for x in range(len(ingredient_amount)):
        mengentest = c.execute(
            "SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ? AND Zutaten.Mengenlevel<?",
            (bottle_number[x], ingredient_amount[x]),
        ).fetchone()
        if mengentest is not None:
            mangelzutat = mengentest[0]
            standartbox(
                f"Es ist in Flasche {bottle_number[x]} mit der Zutat {mangelzutat} nicht mehr genug Volumen vorhanden, {ingredient_amount[x]:.0f} ml wird benötigt!"
            )
            w.tabWidget.setCurrentIndex(3)
            return

    # Generate the Comment for the end of the Programm
    if len(commentlist) > 0:
        zusatzstring = "\n\nNoch hinzufügen:"
        for name_, amount, alcoholic, incredient_id in commentlist:
            alcohol_multiplier = alcohol_faktor if alcoholic == 1 else 1
            zusatzstring += f"\n- ca. {int(amount) * alcohol_multiplier * volume_multiplier:.0f} ml {name_}"
    # search for the longest time
    T_max = max(pump_times)
    T_aktuell = 0
    w.progressionqwindow()
    # activate the pins
    for pin in used_pins:
        if not devenvironment:
            GPIO.setup(pin, GPIO.OUT)
        print(f"Pin: {pin} wurde initialisiert")
    # Until the max time is reached check which channel still needs to be opened
    while T_aktuell < T_max and globals.loopcheck:
        if (T_aktuell) % 1 == 0:
            print(f"{T_aktuell} von {T_max} Sekunden")
        w.prow_change(T_aktuell / T_max * 100)

        iterators = zip(bottle_number, pump_times, pump_volume_flows, used_pins)
        for number, (bottle, pump_time, volume_flow, pin) in enumerate(iterators):
            if pump_time > T_aktuell:
                if (T_aktuell) % 1 == 0:
                    print(f"Pin: {pin} aktiv, aktuelles Volumen: {round(volume_flow*T_aktuell, 1)}")
                if not devenvironment:
                    GPIO.output(pin, 0)
                consumption_ingredients[number] += volume_flow * timestep
            else:
                if (T_aktuell) % 1 == 0:
                    print(f"Pin: {pin} geschlossen!")
                if not devenvironment:
                    GPIO.output(pin, 1)
        T_aktuell += timestep
        T_aktuell = round(T_aktuell, 2)
        time.sleep(timestep)
        qApp.processEvents()
    # Due to safety, each channel is closed at the end
    print("-- Ende --")
    for pin in used_pins:
        print(f"Pin: {pin} wurde geschlossen")
        if not devenvironment:
            GPIO.output(pin, 1)
    w.prow_close()
    # Adds the usage and the cocktail
    c.execute(
        "UPDATE OR IGNORE Rezepte SET Anzahl_Lifetime = Anzahl_Lifetime + 1, Anzahl = Anzahl + 1 WHERE ID = ?",
        (CocktailID,),
    )
    # logs all value, checks if recipe was interrupted and where
    mengenstring = f"{cocktail_volume} ml"
    if globals.loopcheck == False:
        abbruchstring = f" - Rezept wurde bei {round(T_aktuell, 1)} s abgebrochen - {round(cocktail_volume * (T_aktuell + timestep) / T_max)}  ml"
    else:
        abbruchstring = ""
    logger = logging.getLogger("cocktail_application")
    logger.info(f"{mengenstring:8} | {cocktailname}{abbruchstring}")
    print("Verbrauchsmengen: ", [round(x) for x in consumption_ingredients])
    # Updates the consumption, first for the normal values and then if the recipe was not interrupted and handadds exists also for them
    for (consumption, bottle) in zip(consumption_ingredients, bottle_number):
        c.execute(
            "UPDATE OR IGNORE Zutaten SET Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ?, Mengenlevel = Mengenlevel - ? WHERE ID = (SELECT ID FROM Belegung WHERE Flasche = ?)",
            (round(consumption), round(consumption), round(consumption), bottle,),
        )
    if globals.loopcheck:
        for incredient_id, consumption in hand_consumption:
            real_consumption = round(consumption * volume_multiplier)
            print(real_consumption)
            c.execute(
                "UPDATE OR IGNORE Zutaten SET Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ? WHERE ID = ?",
                (real_consumption, real_consumption, incredient_id),
            )
    DB.commit()
    Belegung_progressbar(w, DB, c)
    if globals.loopcheck:
        standartbox(f"Der Cocktail ist fertig! Bitte kurz warten, falls noch etwas nachtropft.{zusatzstring}")
    elif not globals.loopcheck:
        standartbox("Der Cocktail wurde abgebrochen!")
    Maker_nullProB(w, DB, c)
    globals.startcheck = False


@logfunction
def abbrechen_R():
    """ Interrupts the cocktail preparation. """
    globals.loopcheck = False
    print("Rezept wird abgebrochen!")


@logerror
def Maker_nullProB(w, DB, c):
    """ Sets the alcoholintensity to default value (100 %). """
    w.HSIntensity.setValue(0)


@logerror
def Maker_ProB_change(w, DB, c):
    """ Recalculates the alcoholpercentage of the drink with the adjusted Value from the slider. """
    # only carries out if there is a selected recipe
    if w.LWMaker.selectedItems():
        # gets the factor and the recipe ID
        factor = 1 + (w.HSIntensity.value() / 100)
        cocktailname = w.LWMaker.currentItem().text()
        recipe_id = c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (cocktailname,)).fetchone()[0]
        # select amount and concentration for each recipe
        ingredient_data = c.execute(
            "SELECT Zusammen.Menge, Zutaten.Alkoholgehalt FROM Zusammen INNER JOIN Zutaten ON Zutaten.ID = Zusammen.Zutaten_ID WHERE Zusammen.Rezept_ID = ?",
            (recipe_id,),
        )
        sum_volume = 0
        sum_volumeconcentration = 0
        # summs each volume and volumeconcentration up, multiply by the alcoholfactor, if the ingredient is alcoholic
        for row in ingredient_data:
            factor_volume = 1 if row[1] == 0 else factor
            sum_volume += row[0] * factor_volume
            sum_volumeconcentration += row[0] * row[1] * factor_volume
        concentration = sum_volumeconcentration / sum_volume
        w.LAlkoholgehalt.setText("Alkohol: {:.0f}%".format(concentration))
