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

import globals
from maker import Rezepte_a_M, Maker_List_null
from msgboxgenerate import standartbox


def ZutatenCB_Rezepte(w, DB, c):
    """ Asigns all incredients to the Comboboxes in the recipe tab """
    for box in range(1, 9):
        Zspeicher = c.execute("SELECT NAME FROM Zutaten")
        CBRname = getattr(w, "CBR" + str(box))
        CBRname.clear()
        CBRname.addItem("")
        # print(CBRname)
        for row in Zspeicher:
            CBRname.addItem(row[0])
            # print(row[0])


def Rezept_eintragen(w, DB, c, newrecipe):
    """ Enter a new recipe into the DB, if all values are given an logical. \n
    There can be up to 8 different incredients for each recipe. \n
    To store the values into the DB, a many to many relation is used. \n
    The newrecipe dertermines if the recipe is a new one, or an old is being updated
    """
    # die Check Variabeln sind um zu überprüfen, ob eine Eingabe falsch ist, solange = 0 keine Eingabe falsch
    val_check = 0
    neuername = w.LECocktail.text()
    # überprüft ob der Cocktailname eingetragen wurde
    if (neuername == "" or neuername == 0):
        val_check = 1
        standartbox("Bitte Cocktailnamen eingeben!")
    for check_v in range(1, 9):
        CBRname = getattr(w, "CBR" + str(check_v))
        LERname = getattr(w, "LER" + str(check_v))
        # Überprüft ob beide Felder ausgefüllt sind (entweder beide einen wert oder keine einen Wert)
        if ((CBRname.currentText() != "") and LERname.text() == "") or ((CBRname.currentText() == "") and LERname.text() != ""):
            val_check = 1
            standartbox("Irgendwo ist ein Wert vergessen worden!")
            break
        else:
            # überprüft ob die Eingabe eine Zahl ist
            if LERname.text() != "":
                try:
                    int(LERname.text())
                except ValueError:
                    val_check = 1
                    standartbox("Menge muss eine Zahl sein!")
                    break
    # Wenn alle Eingaben stimmen, wird nach dopplungen überprüft
    if val_check == 0:
        Zutaten_V = []
        Mengen_V = []
        # Zusätzlich werden Vektoren (Listen) mit den eingetragenen Werten gebildet
        for check_v in range(1, 9):
            CBRname = getattr(w, "CBR" + str(check_v))
            LERname = getattr(w, "LER" + str(check_v))
            if CBRname.currentText() != "":
                Zutaten_V.append(CBRname.currentText())
                Mengen_V.append(int(LERname.text()))
                # print(CBRname.currentText())
        # print(len(Zutaten_V))
        for Flaschen_i in range(0, len(Zutaten_V)):
            for Flaschen_j in range(0, len(Zutaten_V)):
                if ((Zutaten_V[Flaschen_i] == Zutaten_V[Flaschen_j]) and (Flaschen_i != Flaschen_j)):
                    standartbox("Eine der Zutaten:\n<{}>\nwurde doppelt verwendet!".format(Zutaten_V[Flaschen_i]))
                    val_check = 1
                    break
            if val_check == 1:
                break
    # checks if there is at least one incredient, else this would make no sense
    if val_check == 0:
        if len(Zutaten_V) < 1:
            val_check = 1
            standartbox("Es muss mindestens eine Zutat eingetragen sein!")
    # Checks if both Commentvalues are given (or none) and if they are, if they are numbers
    if val_check == 0:
        if (w.LEmenge_a.text() != "" and w.LEprozent_a.text() == "") or (w.LEmenge_a.text() == "" and w.LEprozent_a.text() != ""):
            val_check = 1
            standartbox("Bei den Kommentarwerten muss sowohl die Menge, als auch die Konzentration eingegeben werden!")
        elif (w.LEmenge_a.text() != "" and w.LEprozent_a.text() != ""):
            try:
                int(w.LEmenge_a.text())
                int(w.LEprozent_a.text())
            except ValueError:
                val_check = 1
                standartbox("Bei den Kommentarwerten wurde mindestens einmal keine Zahl eingegeben!")
    # Hier wird noch überprüft, ob das Rezept schon in der DB existiert, um Dopplungen zu vermeiden (wäre sowieso nicht möglich, da unique DB entry)
    if val_check == 0 and newrecipe:
        c.execute("SELECT COUNT(*) FROM Rezepte WHERE Name=?",(neuername,))
        val_check = c.fetchone()[0]
        if not val_check == 0:
            standartbox("Dieser Name existiert schon in der Datenbank!")
    # Wenn alle Werte Richtig eingetragen wurden, wird angefangen in die DB einzutragen 
    if val_check == 0:
        if not newrecipe:
            altername = w.LWRezepte.currentItem().text()
            c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (altername,))
            CocktailID = c.fetchone()[0]
        SVol = 0
        SVolcon = 0
        SVol_alk = 0
        SVolcon_alk = 0
        # Bilden des Alkoholgehalt vom Cocktail aus einzelnen Zutaten
        for Anzahl in range(0, len(Zutaten_V)):
            c.execute("SELECT Alkoholgehalt FROM Zutaten WHERE Name = ?", (Zutaten_V[Anzahl],))
            Konzentration = c.fetchone()[0]
            Volcon = Mengen_V[Anzahl]*int(Konzentration)
            if Konzentration > 0:
                SVol_alk += Mengen_V[Anzahl]
                SVolcon_alk += Volcon
            SVol += Mengen_V[Anzahl]
            SVolcon +=  Volcon
        SVol2 = SVol
        c_com = 0
        v_com = 0
        # includes the Concentration and Amount if there was a Comment
        if w.LEmenge_a.text() != "":
            SVol2 += int(w.LEmenge_a.text())
            v_com = int(w.LEmenge_a.text())
            SVolcon += int(w.LEmenge_a.text())*int(w.LEprozent_a.text())
            c_com = int(w.LEprozent_a.text())
        Alkoholgehalt_Cocktail = int(SVolcon/SVol2)
        # for none alcoholic recipes, you can't devide by zero (SVol_alk is zero if there is no alcohol)
        if SVol_alk > 0:
            c_alk = int(SVolcon_alk/SVol_alk)
        else:
            c_alk = 0
        v_alk = SVol_alk
        if w.CHBenabled.isChecked():
            isenabled = 1
        else:
            isenabled = 0
        # print(Alkoholgehalt_Cocktail)
        # Rezept wird in Rezept DB eingetragen
        if newrecipe:
            c.execute("INSERT OR IGNORE INTO Rezepte(Name, Alkoholgehalt, Menge, Kommentar, Anzahl_Lifetime, Anzahl, Enabled, V_Alk, c_Alk, V_Com, c_Com) VALUES (?,?,?,?,0,0,?,?,?,?,?)",
                      (neuername, Alkoholgehalt_Cocktail, SVol, w.LEKommentar.text(), isenabled, v_alk, c_alk, v_com, c_com))
        if not newrecipe:
            c.execute("UPDATE OR IGNORE Rezepte SET Name = ?, Alkoholgehalt = ?, Menge = ?, Kommentar = ?, Enabled = ?, V_Alk = ?, c_Alk = ?, V_Com = ?, c_Com = ? WHERE ID = ?",
                      (neuername, Alkoholgehalt_Cocktail, SVol, w.LEKommentar.text(), isenabled, v_alk, c_alk, v_com, c_com, int(CocktailID)))
            c.execute("DELETE FROM Zusammen WHERE Rezept_ID = ?", (CocktailID,))
        # RezeptID, Alkoholisch sowie ZutatenIDs werden herausgesucht und anschließend in die Zusammen DB eingetragen
        c.execute("SELECT ID FROM Rezepte WHERE Name = ?", (neuername,))
        RezepteDBID = c.fetchone()[0]
        for Anzahl in range(0, len(Zutaten_V)):
            temp1 = c.execute(
                "SELECT ID, Alkoholgehalt FROM Zutaten WHERE Name = ?", (Zutaten_V[Anzahl],))
            for temp3 in temp1:
                ZutatenDBID = temp3[0]
                if temp3[1] > 0:
                    isalkoholic = 1
                else:
                    isalkoholic = 0
            print(RezepteDBID, ZutatenDBID, Mengen_V[Anzahl], isalkoholic)
            c.execute("INSERT OR IGNORE INTO Zusammen(Rezept_ID, Zutaten_ID, Menge, Alkoholisch) VALUES (?, ?, ?, ?)",
                      (RezepteDBID, ZutatenDBID, Mengen_V[Anzahl], isalkoholic))
        DB.commit()
        # Entfernen/Zurücksetzen der Labels und Comboboxen
        # hier wird einmal im auskommentierten nur hinzugefügt, alternative diese Zeile und sotieren Befehl
        Rezepte_a_M(w, DB, c)
        Rezepte_a_R(w, DB, c)
        Rezepte_clear(w, DB, c, True)
        if newrecipe:
            standartbox("Rezept unter der ID und dem Namen:\n<{}> <{}>\neingetragen!".format(RezepteDBID, neuername))
        else:
            standartbox("Rezept mit der ID und dem Namen:\n<{}> <{}>\nunter dem Namen:\n<{}>\naktualisiert!".format(RezepteDBID, altername, neuername))


def Rezepte_a_R(w, DB, c):
    """ Updates the ListWidget in the recipe Tab. """
    w.LWRezepte.clear()
    Zspeicher = c.execute("SELECT Name FROM Rezepte")
    for Werte in Zspeicher:
        w.LWRezepte.addItem(Werte[0])


def Rezepte_clear(w, DB, c, clearmode):
    """ Clear all entries out of the Boxes and Comboboxes in the recipe tab. \n
    ------------------------------------------------------------
    Also two different clearmode are available: \n
    False:  just clears the CB and Boxes \n
    True:   also clears the LW selection as well as the helper fields for excact Alkohol Calculation
    """
    # Anmerkung an mich; Rezepte_clear2 ist das alte mit false | Rezepte_clear ist das alte mit true
    w.LECocktail.clear()
    w.LEKommentar.clear()
    if clearmode:
        w.LWRezepte.clearSelection()
    for check_v in range(1, 9):
        CBRname = getattr(w, "CBR" + str(check_v))
        LERname = getattr(w, "LER" + str(check_v))
        LERname.clear()
        w.LEmenge_a.clear()
        w.LEprozent_a.clear()
        CBRname.setCurrentIndex(0)


def Rezepte_Rezepte_click(w, DB, c):
    """ Loads all Data from the recipe DB into the according Fields in the recipe tab. """
    if w.LWRezepte.selectedItems():
        LVZutat = []
        LVMenge = []
        # nimmt zutatenname und Menge für das Rezept
        Zspeicher = c.execute("SELECT Zutaten.Name, Zusammen.Menge FROM Zusammen INNER JOIN Rezepte ON Rezepte.ID=Zusammen.Rezept_ID INNER JOIN Zutaten ON Zusammen.Zutaten_ID=Zutaten.ID WHERE Rezepte.Name = ?", (w.LWRezepte.currentItem().text(),))
        Rezepte_clear(w, DB, c, False)
        # Diese werden dann in ein Vektor (Liste) zugewisen
        for row in Zspeicher:
            #print(row[0], row[1])
            LVZutat.append(row[0])
            LVMenge.append(row[1])
        # füllen aller Werte in die Felder
        for row in range(0, len(LVZutat)):
            LERname = getattr(w, "LER" + str(row + 1))
            LERname.setText(str(LVMenge[row]))
            CBRname = getattr(w, "CBR" + str(row + 1))
            index = CBRname.findText(LVZutat[row], Qt.MatchFixedString)
            CBRname.setCurrentIndex(index)
        # eintragen vom Kommentaren und Titel
        w.LECocktail.setText(str(w.LWRezepte.currentItem().text()))
        Zspeicher = c.execute("SELECT Kommentar, Enabled, V_Com, c_Com FROM Rezepte WHERE Name = ?",
                (w.LWRezepte.currentItem().text(),))
        for row in Zspeicher:
            if row[0] != None:
                w.LEKommentar.setText(str(row[0]))
            enabled = row[1]
            w.LEmenge_a.setText(str(row[2]))
            w.LEprozent_a.setText(str(row[3]))
        if enabled:
            w.CHBenabled.setChecked(True)
        else:
            w.CHBenabled.setChecked(False)


def Rezepte_delete(w, DB, c):
    """ Deletes the selected recipe, requires the Password """
    if w.LEpw.text() == globals.masterpassword:
        if not w.LWRezepte.selectedItems():
            standartbox("Kein Rezept ausgewählt!")
        else:
            Rname = w.LWRezepte.currentItem().text()
            Zspeicher = c.execute(
                "SELECT ID FROM Rezepte WHERE Name = ?", (Rname,))
            for row in Zspeicher:
                CocktailID = row[0]
            # print(CocktailID)
            c.execute("DELETE FROM Zusammen WHERE Rezept_ID = ?", (CocktailID,))
            c.execute("DELETE FROM Rezepte WHERE ID = ?", (CocktailID,))
            DB.commit()
            Rezepte_a_R(w, DB, c)
            Rezepte_a_M(w, DB, c)
            Maker_List_null(w, DB, c)
            Rezepte_clear(w, DB, c, False)
            standartbox("Rezept mit der ID und dem Namen:\n<{}> <{}>\ngelöscht!".format(Rname, CocktailID))
    else:
        print("Falsches Passwort!")
    w.LEpw.setText("")


def save_Rezepte(w, DB, c):
    if w.LEpw.text() == globals.masterpassword:
        with open('Rezepte_export.csv', mode='a', newline='') as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=',')
            csv_writer.writerow(
                ["----- Neuer Export von %s -----" % datetime.date.today()])
            row1 = []
            row2 = []
            Zspeicher = c.execute(
                "SELECT Name, Anzahl FROM Rezepte WHERE Anzahl > 0 ORDER BY Anzahl DESC, Name ASC")
            for row in Zspeicher:
                row1.append(row[0])
                row2.append(row[1])
            csv_writer.writerow(row1)
            csv_writer.writerow(row2)
            csv_writer.writerow(["----- Gesamte Mengen über Lebenszeit -----"])
            row1 = []
            row2 = []
            Zspeicher = c.execute(
                "SELECT Name, Anzahl_Lifetime FROM Rezepte WHERE Anzahl_Lifetime > 0 ORDER BY Anzahl_Lifetime DESC, Name ASC")
            for row in Zspeicher:
                row1.append(row[0])
                row2.append(row[1])
            csv_writer.writerow(row1)
            csv_writer.writerow(row2)
            csv_writer.writerow([" "])
        c.execute("UPDATE OR IGNORE Rezepte SET Anzahl = 0")
        DB.commit()
        standartbox(
            "Alle Daten wurden exportiert und die zurücksetzbare Rezeptanzahl zurückgesetzt!")
    else:
        standartbox("Falsches Passwort!")
    w.LEpw.clear()

def enableall(w, DB, c):
    c.execute("UPDATE OR IGNORE Rezepte SET Enabled = 1")
    DB.commit()
    Rezepte_a_M(w, DB, c)
    Rezepte_clear(w, DB, c, False)
    standartbox("Alle Rezepte wurden wieder aktiv gesetzt!")