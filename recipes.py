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
from maker import Rezepte_a_M, Maker_List_null
from msgboxgenerate import standartbox
from loggerconfig import logfunction, logerror


@logerror
def ZutatenCB_Rezepte(w, DB, c):
    """ Asigns all ingredients to the Comboboxes in the recipe tab """
    for box in range(1, 9):
        cursor_buffer = c.execute("SELECT NAME FROM Zutaten WHERE Hand = 0")
        CBRname = getattr(w, "CBR" + str(box))
        CBRname.clear()
        CBRname.addItem("")
        for row in cursor_buffer:
            CBRname.addItem(row[0])


@logerror
def Rezept_eintragen(w, DB, c, newrecipe):
    """ Enter a new recipe into the DB, if all values are given an logical. \n
    There can be up to 8 different ingredients for each recipe. \n
    To store the values into the DB, a many to many relation is used. \n
    The newrecipe dertermines if the recipe is a new one, or an old is being updated
    """
    # val_check if triggered (eg = 1) if any condition is not met
    val_check = 0
    neuername = w.LECocktail.text()
    # checks if the user pressed change without selecting a recipe first
    if val_check == 0 and not newrecipe and not w.LWRezepte.selectedItems():
        val_check = 1
        standartbox("Es ist kein Rezept ausgewählt!")
    # Checking if Cocktailname is missing
    if val_check == 0 and (neuername == "" or neuername == 0):
        val_check = 1
        standartbox("Bitte Cocktailnamen eingeben!")
    # Checking if both values are given (ingredient and quantity)
    if val_check == 0:
        for check_v in range(1, 9):
            CBRname = getattr(w, "CBR" + str(check_v))
            LERname = getattr(w, "LER" + str(check_v))
            if ((CBRname.currentText() != "") and LERname.text() == "") or (
                (CBRname.currentText() == "") and LERname.text() != ""
            ):
                val_check = 1
                standartbox("Irgendwo ist ein Wert vergessen worden!")
                break
            else:
                # Checks if quantity is a number
                if LERname.text() != "":
                    try:
                        int(LERname.text())
                    except ValueError:
                        val_check = 1
                        standartbox("Menge muss eine Zahl sein!")
                        break
    # Checks, if any ingredient was used twice
    if val_check == 0:
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
            val_check = 1
            standartbox("Eine der Zutaten:\n<{}>\nwurde doppelt verwendet!".format(double_ing[0]))
    # checks if there is at least one ingredient, else this would make no sense
    if val_check == 0:
        if len(Zutaten_V) < 1:
            val_check = 1
            standartbox("Es muss mindestens eine Zutat eingetragen sein!")
    # Checks if the name of the recipe already exists in case of a new recipe
    if val_check == 0 and newrecipe:
        c.execute("SELECT COUNT(*) FROM Rezepte WHERE Name=?", (neuername,))
        val_check = c.fetchone()[0]
        if not val_check == 0:
            standartbox("Dieser Name existiert schon in der Datenbank!")
    # If nothing is wrong, starts writing into DB
    if val_check == 0:
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
                (
                    neuername,
                    Alkoholgehalt_Cocktail,
                    SVol,
                    w.LEKommentar.text(),
                    isenabled,
                    v_alk,
                    c_alk,
                    v_com,
                    c_com,
                    int(CocktailID),
                ),
            )
            c.execute("DELETE FROM Zusammen WHERE Rezept_ID = ?", (CocktailID,))
        # RezeptID, Alkoholisch and ZutatenIDs gets inserted into Zusammen DB
        RezepteDBID = c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (neuername,)).fetchone()[0]
        for Anzahl in range(0, len(Zutaten_V)):
            incproperties = c.execute(
                "SELECT ID, Alkoholgehalt FROM Zutaten WHERE Name = ?", (Zutaten_V[Anzahl],)
            ).fetchone()
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
        Rezepte_a_M(w, DB, c, False, "add", RezepteDBID, isenabled)
        Rezepte_clear(w, DB, c, True)
        if newrecipe:
            standartbox("Rezept unter der ID und dem Namen:\n<{}> <{}>\neingetragen!".format(RezepteDBID, neuername))
        else:
            standartbox(
                "Rezept mit der ID und dem Namen:\n<{}> <{}>\nunter dem Namen:\n<{}>\naktualisiert!".format(
                    RezepteDBID, altername, neuername
                )
            )


@logerror
def Rezepte_a_R(w, DB, c):
    """ Updates the ListWidget in the recipe Tab. """
    w.LWRezepte.clear()
    cursor_buffer = c.execute("SELECT Name FROM Rezepte")
    for values in cursor_buffer:
        w.LWRezepte.addItem(values[0])


@logerror
def Rezepte_clear(w, DB, c, clearmode):
    """ Clear all entries out of the Boxes and Comboboxes in the recipe tab. \n
    ------------------------------------------------------------
    Also two different clearmode are available: \n
    False:  just clears the CB and Boxes \n
    True:   also clears the LW selection as well as the helper fields for excact Alkohol Calculation
    """
    w.LECocktail.clear()
    w.LEKommentar.clear()
    if clearmode:
        w.LWRezepte.clearSelection()
    for check_v in range(1, 9):
        CBRname = getattr(w, "CBR" + str(check_v))
        LERname = getattr(w, "LER" + str(check_v))
        LERname.clear()
        CBRname.setCurrentIndex(0)
    # resets the list which contains the properties of the handadd ingredients
    w.handaddlist = []


@logerror
def Rezepte_Rezepte_click(w, DB, c):
    """ Loads all Data from the recipe DB into the according Fields in the recipe tab. """
    if w.LWRezepte.selectedItems():
        ingredient_names = []
        ingredient_volume = []
        cocktailname = str(w.LWRezepte.currentItem().text())
        # Gets all the ingredients as well the quatities for the recipe from the DB
        cursor_buffer = c.execute(
            "SELECT Zutaten.Name, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ? AND Zusammen.Hand=0",
            (cocktailname,),
        )
        Rezepte_clear(w, DB, c, False)
        # Appends the Values to a List then fills them into the Fields
        for row in cursor_buffer:
            ingredient_names.append(row[0])
            ingredient_volume.append(row[1])
        for row in range(0, len(ingredient_names)):
            LERname = getattr(w, "LER" + str(row + 1))
            LERname.setText(str(ingredient_volume[row]))
            CBRname = getattr(w, "CBR" + str(row + 1))
            index = CBRname.findText(ingredient_names[row], Qt.MatchFixedString)
            CBRname.setCurrentIndex(index)
        # Inserts into Labels
        w.LECocktail.setText(cocktailname)
        # get all the data to write all the extra adds via hand
        cursor_buffer = c.execute(
            "SELECT Zutaten.Name, Zusammen.Menge, Zutaten.ID, Zusammen.Alkoholisch, Zutaten.Alkoholgehalt FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ? AND Zusammen.Hand=1",
            (cocktailname,),
        )
        handcomment = ""
        for row in cursor_buffer:
            handcomment += "{} ml {}, ".format(row[1], row[0])
            w.handaddlist.append([row[2], row[1], row[3], 1, row[4]])
        # at the end substract the last space and column
        if len(handcomment) > 0:
            handcomment = handcomment[:-2]
        w.LEKommentar.setText(handcomment)
        # gets the enabled status
        enabled = c.execute("SELECT Enabled FROM Rezepte WHERE Name = ?", (cocktailname,)).fetchone()[0]
        if enabled:
            w.CHBenabled.setChecked(True)
        else:
            w.CHBenabled.setChecked(False)


@logerror
def Rezepte_delete(w, DB, c):
    """ Deletes the selected recipe, requires the Password """
    if w.LEpw.text() == globals.masterpassword:
        if not w.LWRezepte.selectedItems():
            standartbox("Kein Rezept ausgewählt!")
        else:
            Rname = w.LWRezepte.currentItem().text()
            CocktailID = c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (Rname,)).fetchone()[0]
            c.execute("DELETE FROM Zusammen WHERE Rezept_ID = ?", (CocktailID,))
            c.execute("DELETE FROM Rezepte WHERE ID = ?", (CocktailID,))
            DB.commit()
            w.LWRezepte.clearSelection()
            delfind = w.LWRezepte.findItems(Rname, Qt.MatchExactly)
            if len(delfind) > 0:
                for item in delfind:
                    w.LWRezepte.takeItem(w.LWRezepte.row(item))
            delfind = w.LWMaker.findItems(Rname, Qt.MatchExactly)
            if len(delfind) > 0:
                for item in delfind:
                    w.LWMaker.takeItem(w.LWMaker.row(item))
            for i in range(w.LWMaker.count()):
                w.LWMaker.item(i).setSelected(False)
            for i in range(w.LWRezepte.count()):
                w.LWRezepte.item(i).setSelected(False)
            Rezepte_clear(w, DB, c, False)
            Maker_List_null(w, DB, c)
            standartbox("Rezept mit der ID und dem Namen:\n<{}> <{}>\ngelöscht!".format(Rname, CocktailID))
    else:
        standartbox("Falsches Passwort!")
    w.LEpw.setText("")


@logerror
def enableall(w, DB, c):
    idinput = []
    cursor_buffer = c.execute("SELECT ID FROM Rezepte WHERE Enabled = 0")
    for values in cursor_buffer:
        idinput.append(int(values[0]))
    c.execute("UPDATE OR IGNORE Rezepte SET Enabled = 1")
    DB.commit()
    Rezepte_a_M(w, DB, c, False, "enable", idinput)
    Rezepte_clear(w, DB, c, False)
    standartbox("Alle Rezepte wurden wieder aktiv gesetzt!")
