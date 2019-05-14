# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the maker Tab.
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

from bottles import Belegung_progressbar
from msgboxgenerate import standartbox

import globals


def Rezepte_a_M(w, DB, c):
    """ Goes through every recipe in the DB and crosscheck its incredients 
    with the actual bottle assignments. \n
    Only display the recipes in the maker tab which match all bottles needed.
    """
    w.LWMaker.clear()
    V_Rezepte = []
    ID_Rezepte = []
    # Alle RezeptIDs herraus suchen
    Zspeicher = c.execute("SELECT ID FROM Rezepte")
    for Werte in Zspeicher:
        V_Rezepte.append(int(Werte[0]))
    for row in V_Rezepte:
        vorhandenvar = 0
        V_Rezepte2 = []
        # Alle ZutatenIDs von einem Rezept suchen
        Zspeicher = c.execute(
            "SELECT Zutaten_ID FROM Zusammen WHERE Rezept_ID = ?", (row,))
        for Werte in Zspeicher:
            V_Rezepte2.append(int(Werte[0]))
        for row2 in V_Rezepte2:
            # Jede Zutat auf ihre Belegung überprüfen
            c.execute("SELECT COUNT(*) FROM Belegung WHERE ID = ?", (row2,))
            Zspeicher2 = c.fetchone()[0]
            if Zspeicher2 == 0:
                vorhandenvar = 1
                break
        # wenn alle Zutaten an einem Slot sind, wird die ID in die Liste mit aufgenommen
        if vorhandenvar == 0:
            ID_Rezepte.append(row)
    # alle möglichen Rezepte werden über ihre ID in Liste eingetragen
    for row in ID_Rezepte:
        Zspeicher = c.execute("SELECT Name FROM Rezepte WHERE ID = ?", (row,))
        for Werte in Zspeicher:
            w.LWMaker.addItem(Werte[0])


def Maker_Rezepte_click(w, DB, c):
    """ Get all the data out of the DB for the selected recipe,
    then assign the strings and values in the TextBoxes on the Maker Sheet.
    """
    # in der DB nach dem Rezept (ID) suchen und über die ID (Zutaten) die Zutaten und die Mengen einspeichern.
    # zusätzlich den Alkoholgehalt des Rezeptes herausssuchen und in die Label schreiben
    Maker_List_null(w, DB, c)
    # sucht den Alkoholgehalt aus der DB und trägt diesen ein
    c.execute("SELECT Alkoholgehalt FROM Rezepte WHERE Name = ?",
              (w.LWMaker.currentItem().text(),))
    Zspeicher = c.fetchone()[0]
    w.LAlkoholgehalt.setText("Alkoholgehalt: " + str(Zspeicher) + "%")
    # Benennt das Rezept
    w.LAlkoholname.setText(w.LWMaker.currentItem().text())
    # Sucht die Rezeptmenge aus der Db und trägt sie ein
    c.execute("SELECT Menge FROM Rezepte WHERE Name = ?",
              (w.LWMaker.currentItem().text(),))
    Zspeicher = c.fetchone()[0]
    w.LMenge.setText("Menge: " + str(Zspeicher) + "ml")
    # sucht das Kommentar aus der DB und trägt diesen ein
    c.execute("SELECT Kommentar FROM Rezepte WHERE Name = ?",
              (w.LWMaker.currentItem().text(),))
    Zspeicher = c.fetchone()[0]
    if Zspeicher is not None:
        if len(Zspeicher) >= 1:
            w.LKommentar.setText("Hinzufügen:   " + str(Zspeicher))
        else:
            w.LKommentar.setText("")
    #Zspeicher = c.execute("SELECT Zusammen.Zutaten_ID, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID WHERE Rezepte.Name = ?",(w.LWMaker.currentItem().text(),))
    Zspeicher = c.execute("SELECT Zutaten.Name, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ?", (w.LWMaker.currentItem().text(),))
    LVZutat = []
    LVMenge = []
    for row in Zspeicher:
        #print(row[0], row[1])
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
        # Dann wird die ID, und Menge/Flaschen Ausgewählt
        if not w.LWMaker.selectedItems():
            print("Kein Rezept ausgewählt!")
            standartbox("Kein Rezept ausgewählt!")
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
            # Die Zutatenmenge und die zugehörige Belegung wird ermittelt und mit dem Faktor die Gesamtmenge berechnet
            Zspeicher = c.execute(
                "SELECT Zusammen.Menge, Belegung.Flasche, Zusammen.Alkoholisch From Zusammen INNER JOIN Belegung ON Zusammen.Zutaten_ID = Belegung.ID WHERE Zusammen.Rezept_ID = ?", (CocktailID,))
            for row in Zspeicher:
                if row[2] == 1:
                    MFaktor = Alkoholfaktor
                else:
                    MFaktor = 1
                print(MFaktor)
                V_ZM.append(round(int(row[0])*MFaktor, 1))
                V_FNr.append(int(row[1]))
                V_Zeit.append(
                    round((int(row[0])*MFaktor)/Volumenstrom[row[1]-1], 2))
                V_Volumen += round(int(row[0])*MFaktor, 1)
                V_Verbrauch.append(0)
            MVH = Cocktailmenge/V_Volumen
            if MVH != 1:
                for x in range(0, len(V_ZM)):
                    V_ZM[x] = round(V_ZM[x]*MVH, 1)
                    V_Zeit[x] = round(V_Zeit[x]*MVH, 1)
                    #print("Zutat %i braucht %1.2f ml" %(x+1, V_ZM[x]))
            # Prüft ob noch genug Menge an Flüssigkeit vorhanden ist
            for x in range(0, len(V_ZM)):
                c.execute(
                    "SELECT COUNT(*) FROM Belegung WHERE Flasche = ? AND Mengenlevel<?", (V_FNr[x], V_ZM[x]))
                Mengentest = c.fetchone()[0]
                if Mengentest != 0:
                    createcheck = False
                    c.execute(
                        "SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?", (V_FNr[x],))
                    mangelzutat = c.fetchone()[0]
                    print("Es ist in Flasche %i mit der Zutat %s nicht mehr genug Volumen vorhanden, %.0f ml wird benötigt!" % (
                        V_FNr[x], mangelzutat, V_ZM[x]))
                    standartbox("Es ist in Flasche %i mit der Zutat %s nicht mehr genug Volumen vorhanden, %.0f ml wird benötigt!" % (
                        V_FNr[x], mangelzutat, V_ZM[x]))
                    w.tabWidget.setCurrentIndex(3)
            # Wenn alle Zutaten vorhanden sind startet das Zubereitungsprogramm.
            if createcheck == True:
                # Generiert die Zusatzstrings für den Enddialog, falls Zusatzzutaten nötig sind
                c.execute("SELECT Kommentar FROM Rezepte WHERE Name = ?",(w.LWMaker.currentItem().text(),))
                Zspeicher = c.fetchone()[0]
                if Zspeicher is not None:
                    if len(Zspeicher) >= 1:
                        mysplitstring = str(Zspeicher).split(',')
                        zusatzstring = "\n\nNoch hinzufügen:"
                        switch = False
                        for x in mysplitstring:
                            if switch:
                                y = x[1:].split(' ')
                            else:
                                switch = True
                                y = x.split(' ')
                            z = "{} ".format(str(round(int(y[0])*MVH))) + ' '.join(y[1:])
                            zusatzstring = zusatzstring + "\n- ca. {}".format(z)
                    else:
                        zusatzstring = ""
                else:
                    zusatzstring = ""
                # Die Zeit berechnet sich aus Division von Menge und Volumenstrom, es wird die längste Zeit gesucht
                T_max = V_Zeit[0]
                for row in range(1, len(V_Zeit)):
                    if T_max < V_Zeit[row]:
                        T_max = V_Zeit[row]
                T_aktuell = 0
                w.progressionqwindow()
                # Aktivieren der PINs
                for row in range(0, len(V_FNr)):
                    if not devenvironment:
                        GPIO.setup(Pinvektor[V_FNr[row] - 1], GPIO.OUT)
                    print(
                        "Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " wurde initialisiert")
                # Solange die aktuelle Zeit kleiner als die Maximalzeit ist, wird überprüft, welche Kanäle noch Volumen fördern müssen, und diese sind offen
                # Dies passiert über die vorher berechnete Fließzeit, bis das Sollvolumen jeder Flüssigkeit erreicht wurde
                while (T_aktuell < T_max and globals.loopcheck):
                    if (T_aktuell*100) % 10 == 0:
                        print(str(T_aktuell) + " von " +
                              str(T_max) + " Sekunden ")
                    w.prow_change(T_aktuell/T_max*100)
                    for row in range(0, len(V_FNr)):
                        if V_Zeit[row] > T_aktuell:
                            if (T_aktuell*100) % 10 == 0:
                                print("Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " aktiv, aktuelles Volumen: " + str(
                                    round(Volumenstrom[V_FNr[row] - 1]*T_aktuell, 1)))
                            if not devenvironment:
                                GPIO.output(Pinvektor[V_FNr[row] - 1], 0)
                            V_Verbrauch[row] += Volumenstrom[V_FNr[row] - 1]*0.01
                        else:
                            if (T_aktuell*100) % 10 == 0:
                                print(
                                    "Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " geschlossen!")
                            if not devenvironment:
                                GPIO.output(Pinvektor[V_FNr[row] - 1], 1)
                    T_aktuell += 0.01
                    T_aktuell = round(T_aktuell, 2)
                    time.sleep(0.01)
                    qApp.processEvents()
                # Aus Sicherheitsgründen wird am Ende jeder verwendete Kanal geschlossen
                for row in range(0, len(V_FNr)):
                    print(
                        "Pin: " + str(Pinvektor[V_FNr[row] - 1]) + " wurde geschlossen")
                    if not devenvironment:
                        GPIO.output(Pinvektor[V_FNr[row] - 1], 1)
                w.prow_close()
                # Wendet den Verbrauch auf die DB an
                for x in range(0, len(V_FNr)):
                    c.execute("UPDATE OR IGNORE Belegung SET Mengenlevel = Mengenlevel - ? WHERE Flasche = ?",
                              (round(V_Verbrauch[x]), V_FNr[x]))
                # kreiert den logger und loggt den Rezeptnamen und Menge
                # bemerkt außerdem wenn das Rezept abgebrochen wurde
                # zudem loggt es die Menge, wo das Rezept abgebrochen wurde
                logger = logging.getLogger()
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
                # logger.info(" %s	| %s%s", mengenstring, w.LWMaker.currentItem().text(), abbruchstring)
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
        # Alle Ports werden reseted
        # Der Cleanup nur am Ende (Beenden des Codes) anstellen, sonst Schließt sich das GUIb
        '''GPIO.cleanup()
        print("Alle Ports wurden gecleant!")'''


def abbrechen_R():
    """ Interrupts the cocktail preparation. """
    # global loopcheck
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
    if operator == "+":
        if int(w.LCustomMenge.text()) < maximal:
            w.LCustomMenge.setText(str(int(w.LCustomMenge.text()) + 25))
    else:
        if int(w.LCustomMenge.text()) > minimal:
            w.LCustomMenge.setText(str(int(w.LCustomMenge.text()) - 25))


def Maker_nullProB(w, DB, c):
    """ Sets the alcoholintensity to default value (100 %). """
    w.HSIntensity.setValue(0)
