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
    V_Rezepte = []
    ID_Rezepte = []
    # Search all ids needed, depending on the mode
    # this differs on the input: changed bottles, add an recipe (or changed) or enabled/disabled a recipe
    if mode == "add":
        V_Rezepte.append(changeid)
    elif mode == "enable":
        V_Rezepte = changeid
    else:
        Zspeicher = c.execute("SELECT ID, Enabled FROM Rezepte")
        for Werte in Zspeicher:
            if Werte[1]:
                V_Rezepte.append(int(Werte[0]))
    # Search all ingredient IDs of the recipe
    # if its only one recipe change and it is not enabled, this part will not be carried out
    if goon:
        for row in V_Rezepte:
            vorhandenvar = 0
            # Generates a list of all Ids of the ingredients needed by the machine for every recipe
            V_Rezepte2 = []
            Zspeicher = c.execute(
                "SELECT Zutaten_ID FROM Zusammen WHERE Rezept_ID = ? AND Hand=0", (row,)
            )
            for Werte in Zspeicher:
                V_Rezepte2.append(int(Werte[0]))
            # Check if all Bottles for the Recipe are Connected, if so adds it to the List
            for row2 in V_Rezepte2:
                c.execute("SELECT COUNT(*) FROM Belegung WHERE ID = ?", (row2,))
                Zspeicher2 = c.fetchone()[0]
                if Zspeicher2 == 0:
                    vorhandenvar = 1
                    break
            # Generates a list of all Ids of the ingredients which needs to be added later by hand
            V_Rezepte2 = []
            Zspeicher = c.execute(
                "SELECT Zutaten_ID FROM Zusammen WHERE Rezept_ID = ? AND Hand=1", (row,)
            )
            for Werte in Zspeicher:
                V_Rezepte2.append(int(Werte[0]))
            # Check if all ingredients for the Recipe are set available (Vorhanden DB got the list), if so adds it to the List
            for row2 in V_Rezepte2:
                c.execute("SELECT COUNT(*) FROM Vorhanden WHERE ID = ?", (row2,))
                Zspeicher2 = c.fetchone()[0]
                if Zspeicher2 == 0:
                    vorhandenvar = 1
                    break
            if vorhandenvar == 0:
                ID_Rezepte.append(row)
        # alle möglichen Rezepte werden über ihre ID in Liste eingetragen
        for row in ID_Rezepte:
            name_ = c.execute(
                "SELECT Name FROM Rezepte WHERE ID = ?", (row,)
            ).fetchone()[0]
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
        Zspeicher = c.execute(
            "SELECT Zutaten.Name, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ? AND Zusammen.Hand=0",
            (cocktailname,),
        )
        LVZutat = []
        LVMenge = []
        # assigns the values to the boxes
        for row in Zspeicher:
            LVZutat.append(row[0])
            LVMenge.append(row[1])
        # generates the additional incredients to add. Therefore fills in a blank line and afterwards a header
        # If there are no additional adds, just skip that part
        Zspeicher = c.execute(
            "SELECT Z.Zutaten_ID, Z.Menge FROM Zusammen AS Z INNER JOIN Rezepte AS R ON R.ID=Z.Rezept_ID WHERE R.Name = ? AND Z.Hand=1",
            (cocktailname,),
        )
        commentlist = []
        for row in Zspeicher:
            commentlist.append(row)
        # if there are any additional ingredients generate the additional entries in the list
        if len(commentlist) > 0:
            LVZutat.extend(["", "Selbst hinzufügen:"])
            LVMenge.extend(["", ""])
            for row in commentlist:
                handname = c.execute(
                    "SELECT Name FROM Zutaten WHERE ID=?", (row[0],)
                ).fetchone()[0]
                LVZutat.append(handname)
                LVMenge.append(row[1])
                zusatzmenge += row[1]
        # Adds up both the machine and manual add volume for the total volume
        Zspeicher = c.execute(
            "SELECT Menge FROM Rezepte WHERE Name = ?", (cocktailname,)
        ).fetchone()[0]
        w.LMenge.setText("Menge: " + str(int(Zspeicher) + zusatzmenge) + " ml")
        # loops through the list and give the string to the labels, also give the "Hinzufügen" another color for better visualibility
        for row in range(0, len(LVZutat)):
            LZname = getattr(w, "LZutat" + str(row + 1))
            LZname.setText(str(LVZutat[row]) + " ")
            LMZname = getattr(w, "LMZutat" + str(row + 1))
            if LVMenge[row] != "":
                LMZname.setText(" " + str(LVMenge[row]) + " ml")
            if LVZutat[row] == "Selbst hinzufügen:":
                LZname.setStyleSheet("color: rgb(170, 170, 170)")


@logerror
def Maker_List_null(w, DB, c):
    """ Removes all the Values out of the Maker List. """
    w.LAlkoholgehalt.setText("")
    w.LAlkoholname.setText("")
    w.LMenge.setText("")
    for check_v in range(1, 11):
        LZname = getattr(w, "LZutat" + str(check_v))
        LZname.setText("")
        LMZname = getattr(w, "LMZutat" + str(check_v))
        LMZname.setText("")
        LZname.setStyleSheet("color: rgb(0, 123, 255)")


@logfunction
def Maker_Zubereiten(w, DB, c, normalcheck, devenvironment):
    """ Starts the Cocktail Making procedure, if not already started.\n
    ------------------------------------------------------------ 
    Two different Modes (normalcheck) are available: \n
    "True:"   Uses the regular amount of Volume \n
    "False:"  Uses the User defined (over the GUI) Volume \n
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

    globals.startcheck = True
    V_ZM = []
    V_FNr = []
    V_Zeit = []
    V_Volumen = 0
    V_Verbrauch = []
    timestep = 0.05
    Fixmenge = int(w.LCustomMenge.text())
    Alkoholfaktor = 1 + (w.HSIntensity.value() / 100)
    MFaktor = 1
    globals.loopcheck = True
    Pinvektor = globals.usedpins
    Volumenstrom = globals.pumpvolume

    # gets the ID and the amount for the recipe
    cocktailname = w.LWMaker.currentItem().text()
    Zspeicher = c.execute(
        "SELECT ID, Menge FROM Rezepte WHERE Name = ?", (cocktailname,)
    ).fetchone()
    CocktailID = Zspeicher[0]
    Cocktailmenge = Zspeicher[1]
    if normalcheck == False:
        Cocktailmenge = Fixmenge
    # gets all the amounts, Bottles and alctype for the recipe
    Zspeicher = c.execute(
        "SELECT Zusammen.Menge, Belegung.Flasche, Zusammen.Alkoholisch From Zusammen INNER JOIN Belegung ON Zusammen.Zutaten_ID = Belegung.ID WHERE Zusammen.Rezept_ID = ? AND Zusammen.Hand=0",
        (CocktailID,),
    )
    for row in Zspeicher:
        # if the ingredient is alcoholic assign the factor
        if row[2] == 1:
            MFaktor = Alkoholfaktor
        else:
            MFaktor = 1
        # creates the list for amount, bottlenumber, time, volume and consumption for each ingredient
        V_ZM.append(round(int(row[0]) * MFaktor, 1))
        V_FNr.append(int(row[1]))
        V_Zeit.append(round((int(row[0]) * MFaktor) / Volumenstrom[row[1] - 1], 2))
        V_Volumen += round(int(row[0]) * MFaktor, 1)
        V_Verbrauch.append(0)
    # If there is a comment, it will be checked, and the quantity of the ingredients will be added to the V_Volumen
    # gets all values from the DB which needed to be added via hand later
    Zspeicher = c.execute(
        "SELECT Zutaten.Name, Z.Menge, Z.Alkoholisch, Zutaten.ID FROM Zusammen AS Z INNER JOIN Rezepte AS R ON R.ID=Z.Rezept_ID INNER JOIN Zutaten ON Z.Zutaten_ID=Zutaten.ID WHERE R.ID = ? AND Z.Hand=1",
        (CocktailID,),
    )
    commentlist = []
    for row in Zspeicher:
        commentlist.append(row)
    zusatzstring = ""
    hand_consumption = []
    for row in commentlist:
        MFaktor = Alkoholfaktor if row[2] == 1 else 1
        hand_volume = round(int(row[1]) * MFaktor, 1)
        hand_consumption.append([row[3], hand_volume])
        V_Volumen += hand_volume
    # Checks it the calculated volume is the desired volume, due to concentrating factors and comments, this can vary
    # Calculates the difference and then adjust all values and the times
    MVH = Cocktailmenge / V_Volumen
    if MVH != 1:
        for x in range(len(V_ZM)):
            V_ZM[x] = round(V_ZM[x] * MVH, 1)
            V_Zeit[x] = round(V_Zeit[x] * MVH, 1)
    # Checks if there is still enough volume in the Bottle
    for x in range(len(V_ZM)):
        mengentest = c.execute(
            "SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ? AND Zutaten.Mengenlevel<?",
            (V_FNr[x], V_ZM[x]),
        ).fetchone()
        if mengentest is not None:
            mangelzutat = mengentest[0]
            standartbox(
                f"Es ist in Flasche {V_FNr[x]} mit der Zutat {mangelzutat} nicht mehr genug Volumen vorhanden, {V_ZM[x]:.0f} ml wird benötigt!"
            )
            w.tabWidget.setCurrentIndex(3)
            return

    # Generate the Comment for the end of the Programm
    if len(commentlist) > 0:
        zusatzstring = "\n\nNoch hinzufügen:"
        for row in commentlist:
            MFaktor = Alkoholfaktor if row[2] == 1 else 1
            zusatzstring += f"\n- ca. {int(row[1]) * MVH * MFaktor:.0f} ml {row[0]}"
    # search for the longest time
    T_max = max(V_Zeit)
    T_aktuell = 0
    w.progressionqwindow()
    # activate the pins
    for row in range(0, len(V_FNr)):
        if not devenvironment:
            GPIO.setup(Pinvektor[V_FNr[row] - 1], GPIO.OUT)
        print(f"Pin: {Pinvektor[V_FNr[row] - 1]} wurde initialisiert")
    # Until the max time is reached check which channel still needs to be opened
    while T_aktuell < T_max and globals.loopcheck:
        if (T_aktuell) % 1 == 0:
            print(f"{T_aktuell} von {T_max} Sekunden")
        w.prow_change(T_aktuell / T_max * 100)
        for row in range(len(V_FNr)):
            if V_Zeit[row] > T_aktuell:
                if (T_aktuell) % 1 == 0:
                    print(
                        f"Pin: {Pinvektor[V_FNr[row] - 1]} aktiv, aktuelles Volumen: {round(Volumenstrom[V_FNr[row] - 1]*T_aktuell, 1)}"
                    )
                if not devenvironment:
                    GPIO.output(Pinvektor[V_FNr[row] - 1], 0)
                V_Verbrauch[row] += Volumenstrom[V_FNr[row] - 1] * timestep
            else:
                if (T_aktuell) % 1 == 0:
                    print(f"Pin: {Pinvektor[V_FNr[row] - 1]} geschlossen!")
                if not devenvironment:
                    GPIO.output(Pinvektor[V_FNr[row] - 1], 1)
        T_aktuell += timestep
        T_aktuell = round(T_aktuell, 2)
        time.sleep(timestep)
        qApp.processEvents()
    # Due to safety, each channel is closed at the end
    print("-- Ende --")
    for row in range(0, len(V_FNr)):
        print(f"Pin: {Pinvektor[V_FNr[row] - 1]} wurde geschlossen")
        if not devenvironment:
            GPIO.output(Pinvektor[V_FNr[row] - 1], 1)
    w.prow_close()
    # Adds the usage and the cocktail
    c.execute(
        "UPDATE OR IGNORE Rezepte SET Anzahl_Lifetime = Anzahl_Lifetime + 1, Anzahl = Anzahl + 1 WHERE ID = ?",
        (CocktailID,),
    )
    # logs all value, checks if recipe was interrupted and where
    mengenstring = str(Cocktailmenge) + " ml"
    if globals.loopcheck == False:
        abbruchstring = f" - Rezept wurde bei {round(T_aktuell, 1)} s abgebrochen - {round(Cocktailmenge * (T_aktuell + timestep) / T_max)}  ml"
    else:
        abbruchstring = ""
    logger = logging.getLogger("cocktail_application")
    logger.info(f"{mengenstring:8} | {cocktailname}{abbruchstring}")
    print("Verbrauchsmengen: ", [round(x) for x in V_Verbrauch])
    # Updates the consumption, first for the normal values and then if the recipe was not interrupted and handadds exists also for them
    for x in range(0, len(V_Verbrauch)):
        c.execute(
            "UPDATE OR IGNORE Zutaten SET Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ?, Mengenlevel = Mengenlevel - ? WHERE ID = (SELECT ID FROM Belegung WHERE Flasche = ?)",
            (
                round(V_Verbrauch[x]),
                round(V_Verbrauch[x]),
                round(V_Verbrauch[x]),
                V_FNr[x],
            ),
        )
    if globals.loopcheck:
        for row in hand_consumption:
            c.execute(
                "UPDATE OR IGNORE Zutaten SET Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ? WHERE ID = ?",
                (round(row[1]), round(row[1]), row[0]),
            )
    DB.commit()
    Belegung_progressbar(w, DB, c)
    if globals.loopcheck:
        standartbox(
            f"Der Cocktail ist fertig! Bitte kurz warten, falls noch etwas nachtropft.{zusatzstring}"
        )
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
        recipe_id = c.execute(
            "SELECT ID FROM Rezepte WHERE Name = ?", (cocktailname,)
        ).fetchone()[0]
        # select amount and concentration for each recipe
        ingredient_data = c.execute(
            "SELECT Zusammen.Menge, Zutaten.Alkoholgehalt FROM Zusammen INNER JOIN Zutaten ON Zutaten.ID = Zusammen.Zutaten_ID WHERE Zusammen.Rezept_ID = ?",
            (recipe_id,),
        )
        sum_volume = 0
        sum_volumeconcentration = 0
        # summs each volume and volumeconcentration up, multiply by the alcoholfactor, if the ingredient is alcoholic
        for row in ingredient_data:
            if row[1] == 0:
                factor_volume = 1
            else:
                factor_volume = factor
            sum_volume += row[0] * factor_volume
            sum_volumeconcentration += row[0] * row[1] * factor_volume
        concentration = sum_volumeconcentration / sum_volume
        w.LAlkoholgehalt.setText("Alkohol: {:.0f}%".format(concentration))
