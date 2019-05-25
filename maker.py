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

import globals


def Rezepte_a_M(w, DB, c, reloadall = True, mode = "", changeid = 0, goon = True):
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
    if goon:
        for row in V_Rezepte:
            vorhandenvar = 0
            V_Rezepte2 = []
            Zspeicher = c.execute(
                "SELECT Zutaten_ID FROM Zusammen WHERE Rezept_ID = ?", (row,))
            for Werte in Zspeicher:
                V_Rezepte2.append(int(Werte[0]))
            # Check if all Bottles for the Recipe are Connected, if so adds it to the List
            for row2 in V_Rezepte2:
                c.execute("SELECT COUNT(*) FROM Belegung WHERE ID = ?", (row2,))
                Zspeicher2 = c.fetchone()[0]
                if Zspeicher2 == 0:
                    vorhandenvar = 1
                    break
            if vorhandenvar == 0:
                ID_Rezepte.append(row)
        # alle möglichen Rezepte werden über ihre ID in Liste eingetragen
        for row in ID_Rezepte:
            name_ = c.execute("SELECT Name FROM Rezepte WHERE ID = ?", (row,)).fetchone()[0]
            w.LWMaker.addItem(name_)


def Maker_Rezepte_click(w, DB, c):
    """ Get all the data out of the DB for the selected recipe,
    then assign the strings and values in the TextBoxes on the Maker Sheet.
    """
    if w.LWMaker.selectedItems():
        # search the DB for the recipe (ID) over the ID (Zutaten) fetch the ingredients and amount
        Maker_List_null(w, DB, c)
        zusatzmenge = 0
        Maker_ProB_change(w, DB, c)
        # Gets and sets the name
        cocktailname = w.LWMaker.currentItem().text()
        w.LAlkoholname.setText(cocktailname)
        # look up the comment
        c.execute("SELECT Kommentar FROM Rezepte WHERE Name = ?",
                (cocktailname,))
        Zspeicher = c.fetchone()[0]
        # gets the amount out of the comment
        if Zspeicher is not None:
            if len(Zspeicher) >= 1:
                w.LKommentar.setText("Hinzufügen:  " + str(Zspeicher))
                mysplitstring = re.split(', | |,', Zspeicher) 
                for allwords in mysplitstring:
                    try:
                        zusatzmenge += int(allwords)
                    except:
                        pass
            else:
                w.LKommentar.setText("")
        c.execute("SELECT Menge FROM Rezepte WHERE Name = ?",
                (cocktailname,))
        Zspeicher = c.fetchone()[0]
        w.LMenge.setText("Menge: " + str(int(Zspeicher) + zusatzmenge) + " ml")
        #Zspeicher = c.execute("SELECT Zusammen.Zutaten_ID, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID WHERE Rezepte.Name = ?",(cocktailname,))
        Zspeicher = c.execute("SELECT Zutaten.Name, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ?", (cocktailname,))
        LVZutat = []
        LVMenge = []
        # assigns the values to the boxes
        for row in Zspeicher:
            LVZutat.append(row[0])
            LVMenge.append(row[1])
        for row in range(0, len(LVZutat)):
            LZname = getattr(w, "LZutat" + str(row + 1))
            LZname.setText(str(LVZutat[row]) + " ")
            LMZname = getattr(w, "LMZutat" + str(row + 1))
            LMZname.setText(" " + str(LVMenge[row]) + " ml")


def Maker_List_null(w, DB, c):
    """ Removes all the Values out of the Maker List. """
    w.LAlkoholgehalt.setText("")
    w.LAlkoholname.setText("")
    w.LMenge.setText("")
    w.LKommentar.setText("")
    for check_v in range(1, 9):
        LZname = getattr(w, "LZutat" + str(check_v))
        LZname.setText("")
        LMZname = getattr(w, "LMZutat" + str(check_v))
        LMZname.setText("")


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
    if globals.startcheck == False:
        globals.startcheck = True
        V_ZM = []
        V_FNr = []
        V_Zeit = []
        V_Volumen = 0
        V_Verbrauch = []
        Fixmenge = int(w.LCustomMenge.text())
        Alkoholfaktor = 1 + (w.HSIntensity.value()/100)
        MFaktor = 1
        globals.loopcheck = True
        createcheck = True
        Pinvektor = globals.usedpins
        Volumenstrom = globals.pumpvolume
        if not w.LWMaker.selectedItems():
            standartbox("Kein Rezept ausgewählt!")
        # Select ID, Bottles and amount, calculate the time and update the counter
        else:
            Zspeicher = c.execute(
                "SELECT ID, Menge FROM Rezepte WHERE Name = ?", (w.LWMaker.currentItem().text(),))
            for row in Zspeicher:
                CocktailID = row[0]
                Cocktailmenge = row[1]
            c.execute(
                "UPDATE OR IGNORE Rezepte SET Anzahl_Lifetime = Anzahl_Lifetime + 1, Anzahl = Anzahl + 1 WHERE ID = ?", (CocktailID,))
            if normalcheck == False:
                Cocktailmenge = Fixmenge
            Zspeicher = c.execute(
                "SELECT Zusammen.Menge, Belegung.Flasche, Zusammen.Alkoholisch From Zusammen INNER JOIN Belegung ON Zusammen.Zutaten_ID = Belegung.ID WHERE Zusammen.Rezept_ID = ?", (CocktailID,))
            for row in Zspeicher:
                if row[2] == 1:
                    MFaktor = Alkoholfaktor
                else:
                    MFaktor = 1
                V_ZM.append(round(int(row[0])*MFaktor, 1))
                V_FNr.append(int(row[1]))
                V_Zeit.append(
                    round((int(row[0])*MFaktor)/Volumenstrom[row[1]-1], 2))
                V_Volumen += round(int(row[0])*MFaktor, 1)
                V_Verbrauch.append(0)
            # If there is a comment, it will be checked, and the quantity of the ingredients will be added to the V_Volumen
            c.execute("SELECT Kommentar FROM Rezepte WHERE Name = ?",(w.LWMaker.currentItem().text(),))
            Zspeicher = c.fetchone()[0]
            if Zspeicher is None:
                pass
            elif len(Zspeicher) >= 1:
                mysplitstring = re.split(', | |,', Zspeicher) 
                for allwords in mysplitstring:
                    try:
                        V_Volumen += int(allwords)
                    except:
                        pass
            MVH = Cocktailmenge/V_Volumen
            if MVH != 1:
                for x in range(0, len(V_ZM)):
                    V_ZM[x] = round(V_ZM[x]*MVH, 1)
                    V_Zeit[x] = round(V_Zeit[x]*MVH, 1)
            # Checks if there is still enough volume in the Bottle
            for x in range(0, len(V_ZM)):
                c.execute(
                    "SELECT COUNT(*) FROM Belegung WHERE Flasche = ? AND Mengenlevel<?", (V_FNr[x], V_ZM[x]))
                Mengentest = c.fetchone()[0]
                if Mengentest != 0:
                    createcheck = False
                    c.execute(
                        "SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?", (V_FNr[x],))
                    mangelzutat = c.fetchone()[0]
                    standartbox("Es ist in Flasche %i mit der Zutat %s nicht mehr genug Volumen vorhanden, %.0f ml wird benötigt!" % (
                        V_FNr[x], mangelzutat, V_ZM[x]))
                    w.tabWidget.setCurrentIndex(3)
            # if all conditions are met, go on
            if createcheck == True:
                # Generate the Comment for the end of the Programm
                c.execute("SELECT Kommentar FROM Rezepte WHERE Name = ?",(w.LWMaker.currentItem().text(),))
                Zspeicher = c.fetchone()[0]
                if Zspeicher is not None:
                    if len(Zspeicher) >= 1:
                        mysplitstring = re.split(', |,', str(Zspeicher))
                        zusatzstring = "\n\nNoch hinzufügen:"
                        for x in mysplitstring:
                            y = x.split(' ')
                            z = "{} ".format(str(round(int(y[0])*MVH))) + ' '.join(y[1:])
                            zusatzstring = zusatzstring + "\n- ca. {}".format(z)
                    else:
                        zusatzstring = ""
                else:
                    zusatzstring = ""
                # search for the longest time
                T_max = V_Zeit[0]
                for row in range(1, len(V_Zeit)):
                    if T_max < V_Zeit[row]:
                        T_max = V_Zeit[row]
                T_aktuell = 0
                w.progressionqwindow()
                # activate the pins
                for row in range(0, len(V_FNr)):
                    if not devenvironment:
                        GPIO.setup(Pinvektor[V_FNr[row] - 1], GPIO.OUT)
                    print(
                        "Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " wurde initialisiert")
                # Until the max time is reached check which channel still needs to be opened
                while (T_aktuell < T_max and globals.loopcheck):
                    if (T_aktuell) % 1 == 0:
                        print(str(T_aktuell) + " von " +
                              str(T_max) + " Sekunden ")
                    w.prow_change(T_aktuell/T_max*100)
                    for row in range(0, len(V_FNr)):
                        if V_Zeit[row] > T_aktuell:
                            if (T_aktuell) % 1 == 0:
                                print("Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " aktiv, aktuelles Volumen: " + str(
                                    round(Volumenstrom[V_FNr[row] - 1]*T_aktuell, 1)))
                            if not devenvironment:
                                GPIO.output(Pinvektor[V_FNr[row] - 1], 0)
                            V_Verbrauch[row] += Volumenstrom[V_FNr[row] - 1]*0.01
                        else:
                            if (T_aktuell) % 1 == 0:
                                print(
                                    "Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " geschlossen!")
                            if not devenvironment:
                                GPIO.output(Pinvektor[V_FNr[row] - 1], 1)
                    T_aktuell += 0.01
                    T_aktuell = round(T_aktuell, 2)
                    time.sleep(0.01)
                    qApp.processEvents()
                # Due to safety, each channel is closed at the end
                print("-- Ende --")
                for row in range(0, len(V_FNr)):
                    print(
                        "Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " wurde geschlossen")
                    if not devenvironment:
                        GPIO.output(Pinvektor[V_FNr[row] - 1], 1)
                w.prow_close()
                # Adds the usage
                for x in range(0, len(V_FNr)):
                    c.execute("UPDATE OR IGNORE Belegung SET Mengenlevel = Mengenlevel - ? WHERE Flasche = ?",
                              (round(V_Verbrauch[x]), V_FNr[x]))
                # logs all value, checks if recipe was interrupted and where
                if normalcheck:
                    mengenstring = "Standard"
                else:
                    mengenstring = str(Cocktailmenge) + " ml"
                if globals.loopcheck == False:
                    abbruchstring = " - Rezept wurde bei " + \
                        str(round(T_aktuell, 1)) + " s abgebrochen - " + \
                        str(round(Cocktailmenge*(T_aktuell + 0.01)/T_max)) + " ml"
                else:
                    abbruchstring = ""
                template = "{:8} | {}{}"
                logger = logging.getLogger('cocktail_application')
                logger.info(template.format(
                    mengenstring, w.LWMaker.currentItem().text(), abbruchstring))
                print("Verbrauchsmengen: ", [round(x) for x in V_Verbrauch])
                for x in range(0, len(V_Verbrauch)):
                    c.execute("UPDATE OR IGNORE Zutaten SET Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ? WHERE ID = (SELECT ID FROM Belegung WHERE Flasche = ?)",
                              (round(V_Verbrauch[x]), round(V_Verbrauch[x]), V_FNr[x]))
                DB.commit()
                Belegung_progressbar(w, DB, c)
                if globals.loopcheck:
                    standartbox(
                        "Der Cocktail ist fertig! Bitte kurz warten, falls noch etwas nachtropft.{}".format(zusatzstring))
                elif not globals.loopcheck:
                    standartbox("Der Cocktail wurde abgebrochen!")
        globals.startcheck = False


def abbrechen_R():
    """ Interrupts the cocktail preparation. """
    globals.loopcheck = False
    print("Rezept wird abgebrochen!")


def Maker_pm(w, DB, c, operator):
    """ Increases or decreases the Custom set amount. \n
    The Minimum/Maximum ist 100/400. \n
    ------------------------------------------------------------
    As operater can be used: \n
    "+":    increases the value by 25 \n
    "-":    decreases the value by 25
    """
    minimal = 100
    maximal = 400
    dm = 25
    amount = int(w.LCustomMenge.text())
    if operator == "+" and amount < maximal:
        amount += dm
    if operator == "-" and amount > minimal:
        amount -= dm
    w.LCustomMenge.setText(str(amount))


def Maker_nullProB(w, DB, c):
    """ Sets the alcoholintensity to default value (100 %). """
    w.HSIntensity.setValue(0)


def Maker_ProB_change(w, DB, c):
    """ Recalculates the alcoholpercentage of the drink with the adjusted Value from the slider. """
    if w.LWMaker.selectedItems():
        factor = 1 + (w.HSIntensity.value()/100)
        cocktailname = w.LWMaker.currentItem().text()
        # if the factor is one gets the value out of the DB
        if factor == 1:
            c.execute("SELECT Alkoholgehalt FROM Rezepte WHERE Name = ?",(cocktailname,))
            c_ges = c.fetchone()[0]
        # if the value is not one calculates the new value out of the saved helper values in the DB
        else:
            Zspeicher = c.execute("SELECT Menge, V_Alk, c_Alk, V_Com, c_Com FROM Rezepte WHERE Name = ?",(cocktailname,))
            for row in Zspeicher:
                v_ges = row[0]
                v_alk = row[1]
                c_alk = row[2]
                v_com = row[3]
                c_com = row[4]
            v_notalk = v_ges - v_alk
            v_gesneu = v_alk*factor + v_notalk + v_com
            vc_neu = v_alk*factor*c_alk + v_com*c_com
            c_ges = vc_neu/v_gesneu
        w.LAlkoholgehalt.setText("Alkohol: {:.0f}%".format(c_ges))
