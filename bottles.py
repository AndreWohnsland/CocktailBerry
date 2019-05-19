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

import globals
from msgboxgenerate import standartbox


def ZutatenCB_Belegung(w, DB, c):
    """ Asigns all incredients to the Comboboxes in the bottles tab. """
    for box in range(1, 11):
        Zspeicher = c.execute("SELECT NAME FROM Zutaten")
        CBBname = getattr(w, "CBB" + str(box))
        CBBname.clear()
        CBBname.addItem("")
        for row in Zspeicher:
            CBBname.addItem(row[0])


def Belegung_eintragen(w, DB, c):
    """ Insert the selected Bottleorder into the DB. """
    from maker import Rezepte_a_M
    # prüfen wo der erste Belegungswert Startet (falls der erste, etc. slot leer ist)
    CBB_List = []
    dummy2 = 0
    for Flaschen_C in range(1, 11):
        CBBname = getattr(w, "CBB" + str(Flaschen_C))
        if (CBBname.currentText() != "" and CBBname.currentText() != 0):
            CBB_List.append(CBBname.currentText())
    # Vergleiche alle eingetragenen Werte und prüfe nach einer Doppelung
    # Dummy1 wird 1 falls eine Doppelung eintritt
    for Flaschen_i in range(0, len(CBB_List)):
        for Flaschen_j in range(0, len(CBB_List)):
            if ((CBB_List[Flaschen_i] == CBB_List[Flaschen_j]) and (Flaschen_i != Flaschen_j)):
                dummy2 = 1
                break
    # Wenn keine Dopplung existiert wird in DB eingetragen
    if dummy2 == 0:
        for Flaschen_C in range(1, 11):
            # Memo an mich: Umschreiben, erst id holen, dann alles auf einmal schreiben!
            Speicher_ID2 = 0
            CBBname = getattr(w, "CBB" + str(Flaschen_C))
            c.execute("UPDATE OR IGNORE Belegung SET Zutat_F = ? WHERE Flasche = ?",
                      (CBBname.currentText(), Flaschen_C))
            Speicher_ID = c.execute(
                "SELECT ID FROM Zutaten WHERE Name = ?", (CBBname.currentText(),))
            for row in Speicher_ID:
                Speicher_ID2 = row[0]
            c.execute("UPDATE OR IGNORE Belegung SET ID = ? WHERE Flasche = ?", (int(
                Speicher_ID2), Flaschen_C))
            DB.commit()
        Belegung_a(w, DB, c)
        Rezepte_a_M(w, DB, c)
        Belegung_progressbar(w, DB, c)
        standartbox("Belegung geändert")
    else:
        standartbox("Eine der Zutaten wurde doppelt zugewiesen!")


def Belegung_einlesen(w, DB, c):
    """ Reads the Bottleorder into the BottleTab. """
    for Flaschen_C in range(1, 11):
        CBBname = getattr(w, "CBB" + str(Flaschen_C))
        Testbelegung = c.execute(
            "SELECT Zutat_F FROM Belegung WHERE Flasche=?", (Flaschen_C,))
        for row in Testbelegung:
            index = CBBname.findText(row[0], Qt.MatchFixedString)
            CBBname.setCurrentIndex(index)


def Belegung_a(w, DB, c):
    """ Loads or updates the Labels of the Bottles (Volumelevel). """
    for Flaschen_C in range(1, 11):
        Lname = getattr(w, "LBelegung" + str(Flaschen_C))
        Testbelegung = c.execute(
            "SELECT Zutat_F FROM Belegung WHERE Flasche=?", (Flaschen_C,))
        for row in Testbelegung:
            Lname.setText("  " + str(row[0]) + ":")


def Belegung_Flanwenden(w, DB, c):
    """ Renews all the Bottles which are checked as new. """
    for Flaschen_C in range(1, 11):
        PBname = getattr(w, "PBneu" + str(Flaschen_C))
        if PBname.isChecked():
            storevar = c.execute(
                "SELECT Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?", (Flaschen_C,)).fetchone()
            if storevar is not None:
                storevol = storevar[0]
                c.execute(
                    "UPDATE OR IGNORE Belegung SET Mengenlevel = ? WHERE Flasche = ?", (storevol, Flaschen_C))
    DB.commit()
    for Flaschen_C in range(1, 11):
        PBname = getattr(w, "PBneu" + str(Flaschen_C))
        PBname.setChecked(False)
    Belegung_progressbar(w, DB, c)
    standartbox("Alle Flaschen angewendet!")


def Belegung_progressbar(w, DB, c):
    """ Gets the actual Level of the Bottle and creates the relation to the maximum Level. \n
    Assigns it to the according ProgressBar.
    """
    b1 = []
    storeval = c.execute("SELECT Mengenlevel FROM Belegung")
    for row in storeval:
        b1.append(row[0])
    for x in range(1, 11):
        ProBname = getattr(w, "ProBBelegung" + str(x))
        storeval2 = c.execute(
            "SELECT Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?", (x,))
        for row in storeval2:
            if b1[x-1] <= 0:
                ProBname.setValue(0)
            else:
                ProBname.setValue(b1[x-1]/row[0]*100)


def CleanMachine(w, DB, c, devenvironment):
    """ Activate all Pumps for 20 s to clean them. Needs the Password. """
    if not devenvironment:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
    if w.LECleanMachine.text() == globals.masterpassword:
        standartbox(
            "Achtung!: Maschine wird gereinigt, genug Wasser bereitstellen!")
        logger = logging.getLogger('cocktail_application')
        template = "{:*^80}"
        logger.info(template.format("Cleaning the Pumps",))
        Pinvektor = globals.usedpins
        w.LECleanMachine.clear()
        for row in range(0, 9):
            if not devenvironment:
                GPIO.setup(Pinvektor[row], GPIO.OUT)
        T_aktuell = 0
        while (T_aktuell < 20):
            for row in range(0, 9):
                if not devenvironment:
                    GPIO.output(Pinvektor[row], 0)
            T_aktuell += 0.1
            T_aktuell = round(T_aktuell, 1)
            time.sleep(0.1)
            qApp.processEvents()
        for row in range(0, 9):
            if not devenvironment:
                GPIO.output(Pinvektor[row], 1)
        standartbox("Fertig!!!")
    else:
        standartbox("Falsches Passwort!!!!")
    w.LECleanMachine.setText("")
