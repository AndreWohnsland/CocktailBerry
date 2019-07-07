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
from loggerconfig import logerror, logfunction


def customlevels(w, DB, c):
    """ Opens the additional window to change the volume levels of the bottles. """
    bot_names = []
    vol_values = []
    w.bottleswindow(bot_names, vol_values)

def get_bottle_ingredients(w, DB, c):
    """ At the start of the Programm, get all the ingredients from the DB. """
    for i in range(1,11):
        storeval = c.execute("SELECT Zutaten.Name FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?", (i,)).fetchone()
        if storeval is not None:
            globals.olding.append(storeval[0])
        else:
            globals.olding.append('')


def refresh_bottle_cb(w, DB, c):
    """ This function is each time called, when the index of
    the Bottles Combobox changes. It then evaluates the difference
    between the old and the new bottles and adds/substract the changes 
    ingredient to the dropdowns.
    To prevent a inside loop call of this function, the global supressbox 
    exists. Otherwise if an item is removed, the function will call itself again
    since the index may change itself with the deletion.
    """
    # Creating a list of the new and old bottles used
    if not globals.supressbox:
        globals.supressbox = True
        old_order = globals.olding
        new_order = []
        for i in range(1,11):
            CBBname = getattr(w, "CBB" + str(i))
            if CBBname.currentText() != 0:
                new_order.append(CBBname.currentText())
            else:
                new_order.append("")
        # getting the difference between those two lists and assign new/old value
        new_blist = list(set(new_order) - set(old_order))
        old_blist = list(set(old_order) - set(new_order))
        # checks if the list only contains one element
        # extrtacts the element out of the list
        if len(new_blist)>1 or len(old_blist)>1:
            raise ValueError('The List should never contain two or more Elements!')
        else:
            if len(new_blist)==0:
                new_bottle = ""
            else:
                new_bottle = new_blist[0]
            if len(old_blist)==0:
                old_bottle = ""
            else:
                old_bottle = old_blist[0]
        # adds or substracts the text to the comboboxes (except the one which was changed)
        for i in range(1,11):
            CBBname = getattr(w, "CBB" + str(i))
            if (old_bottle != "") and (old_bottle != old_order[i-1]):
                CBBname.addItem(old_bottle)
            if (new_bottle != "") and (new_bottle != new_order[i-1]):
                index = CBBname.findText(new_bottle, Qt.MatchFixedString)
                if index >= 0:
                    CBBname.removeItem(index)
            CBBname.model().sort(0)
        # the new is now the old for the next step:
        Belegung_eintragen(w, DB, c)
        globals.olding = new_order
        globals.supressbox = False


@logerror
def ZutatenCB_Belegung(w, DB, c):
    """ Asigns all ingredients to the Comboboxes in the bottles tab. 
    DEPRECIATED; Use newCB_Bottles instead!!!
    """
    for box in range(1, 11):
        Zspeicher = c.execute("SELECT NAME FROM Zutaten")
        CBBname = getattr(w, "CBB" + str(box))
        CBBname.clear()
        CBBname.addItem("")
        for row in Zspeicher:
            CBBname.addItem(row[0])


def testfunction(w, DB, c):
    pass


@logerror
def newCB_Bottles(w, DB,c):
    """ This is a new method for the DropDowns of the different Bottles.\n
    Assigns all possible ingredients to the Comboboxes in the bottles tab.\n
    By possible it means that if another Combobox got the value, others cannot use it,
    since each bottle may only be used once in the Configuration.
    Due to the process, after each change, each CB needs to be rechecked.
    """
    # generates a list of all Combobox entries
    entrylist = globals.olding
    inglist = []
    Zspeicher = c.execute("SELECT NAME FROM Zutaten")
    for ing in Zspeicher:
        inglist.append(str(ing[0]))
    # generates a list for each CB which values have to be assigned
    # Therefore substract the already assigned values from all potential values
    # except the value of the current CB
    cblist = []
    for row, _ in enumerate(entrylist):
        cblist.append(sorted(set(inglist) - set([x for i,x in enumerate(entrylist) if i!=row])))
    # finally deletes and refills every box
    for row, endlist in enumerate(cblist):
        CBBname = getattr(w, "CBB" + str(row + 1))
        CBBname.clear()
        CBBname.addItem("")
        for item in endlist:
            CBBname.addItem(item)


@logerror
def Belegung_eintragen(w, DB, c, msgcall=False):
    """ Insert the selected Bottleorder into the DB. """
    # this import is neccecary on module level, otherwise there would be a circular import
    from maker import Rezepte_a_M
    # Checks where are entries and appends them to a list
    CBB_List = []
    dbl_check = 0
    for Flaschen_C in range(1, 11):
        CBBname = getattr(w, "CBB" + str(Flaschen_C))
        if (CBBname.currentText() != "" and CBBname.currentText() != 0):
            CBB_List.append(CBBname.currentText())
    # Checks if any ingredient is used twice, if so, dbl_check gets activated 
    for Flaschen_i in range(0, len(CBB_List)):
        for Flaschen_j in range(0, len(CBB_List)):
            if ((CBB_List[Flaschen_i] == CBB_List[Flaschen_j]) and (Flaschen_i != Flaschen_j)):
                dbl_check = 1
                standartbox("Eine der Zutaten wurde doppelt zugewiesen!")
                break
        if dbl_check == 1:
            break
    # If no error, insert values into DB
    if dbl_check == 0:
        for Flaschen_C in range(1, 11):
            Speicher_ID = 0
            CBBname = getattr(w, "CBB" + str(Flaschen_C))
            ingredientname = CBBname.currentText()
            buffer = c.execute(
                "SELECT ID FROM Zutaten WHERE Name = ?", (ingredientname,))
            for buf in buffer:
                Speicher_ID = buf[0]
            c.execute("UPDATE OR IGNORE Belegung SET ID = ?, Zutat_F = ? WHERE Flasche = ?",
                (int(Speicher_ID), ingredientname, Flaschen_C))
            DB.commit()
        Belegung_a(w, DB, c)
        Rezepte_a_M(w, DB, c)
        Belegung_progressbar(w, DB, c)
        if msgcall:
            standartbox("Belegung wurde geändert!")        


@logerror
def Belegung_einlesen(w, DB, c):
    """ Reads the Bottleorder into the BottleTab. """
    for Flaschen_C in range(1, 11):
        CBBname = getattr(w, "CBB" + str(Flaschen_C))
        Testbelegung = c.execute(
            "SELECT Zutaten.Name FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche=?", (Flaschen_C,))
        for row in Testbelegung:
            index = CBBname.findText(row[0], Qt.MatchFixedString)
            CBBname.setCurrentIndex(index)


@logerror
def Belegung_a(w, DB, c):
    """ Loads or updates the Labels of the Bottles (Volumelevel). """
    for Flaschen_C in range(1, 11):
        Lname = getattr(w, "LBelegung" + str(Flaschen_C))
        Testbelegung = c.execute(
            "SELECT Zutaten.Name FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche=?", (Flaschen_C,)).fetchone()
        # if len(Testbelegung)==0:
        #     Lname.setText("  ")
        # here must some more code to hide labels when there is no incredient in the according slot
        if Testbelegung is not None:
            Lname.setText("  " + str(Testbelegung[0]) + ":")
        else:
            Lname.setText("  -  ")


@logerror
def Belegung_Flanwenden(w, DB, c):
    """ Renews all the Bottles which are checked as new. """
    for Flaschen_C in range(1, 11):
        PBname = getattr(w, "PBneu" + str(Flaschen_C))
        if PBname.isChecked():
            bottleid = c.execute("SELECT ID FROM Belegung WHERE Flasche = ?", (Flaschen_C,)).fetchone()[0]
            # the value can be None if the user checks a not used box, so its captured here
            if bottleid != 0:
                c.execute("UPDATE OR IGNORE Zutaten Set Mengenlevel = Flaschenvolumen WHERE ID = ?", (bottleid,))
    DB.commit()
    # remove all the checks from the combobuttons
    for Flaschen_C in range(1, 11):
        PBname = getattr(w, "PBneu" + str(Flaschen_C))
        PBname.setChecked(False)
    Belegung_progressbar(w, DB, c)
    standartbox("Alle Flaschen angewendet!")


@logerror
def Belegung_progressbar(w, DB, c):
    """ Gets the actual Level of the Bottle and creates the relation to the maximum Level. \n
    Assigns it to the according ProgressBar.
    """
    for Flaschen_C in range(1, 11):
        storeval = c.execute("SELECT Zutaten.Mengenlevel, Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID WHERE Belegung.Flasche = ?", (Flaschen_C,)).fetchone()
        if storeval is not None:
            level = storeval[0]
            maximum = storeval[1]
            ProBname = getattr(w, "ProBBelegung" + str(Flaschen_C))
            # Sets the level of the bar, it cant drop below 0 or 100%
            if level <= 0:
                ProBname.setValue(0)
            elif level/maximum > 1:
                ProBname.setValue(100)
            else:
                ProBname.setValue(level/maximum*100)


@logerror
def CleanMachine(w, DB, c, devenvironment):
    """ Activate all Pumps for 20 s to clean them. Needs the Password. Logs the Event. """
    if not devenvironment:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
    if w.LECleanMachine.text() == globals.masterpassword:
        standartbox(
            "Achtung!: Maschine wird gereinigt, genug Wasser bereitstellen! Ok zum Fortfahren.")
        logger = logging.getLogger('cocktail_application')
        template = "{:*^80}"
        logger.info(template.format("Cleaning the Pumps",))
        Pinvektor = globals.usedpins
        w.LECleanMachine.setText("")
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
