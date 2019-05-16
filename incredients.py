# -*- coding: utf-8 -*-
""" Module with all nececcary functions for the incredients Tab.
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
from bottles import ZutatenCB_Belegung, Belegung_einlesen, Belegung_progressbar
from msgboxgenerate import standartbox

import globals


def Zutat_eintragen(w, DB, c):
    """ Insert the new incredient into the DB, if all values are given 
    and its name is not already in the DB.
    """
    print("Zutat ist: ", w.LEZutatRezept.text())
    print("Alkoholanteil ist: ", w.LEGehaltRezept.text())
    print("Flaschenvolumen ist: ", w.LEFlaschenvolumen.text())
    c.execute("SELECT COUNT(*) FROM Zutaten WHERE Name=?",
              (w.LEZutatRezept.text(),))
    Zutatentest = c.fetchone()[0]
    if (w.LEZutatRezept.text() == "") or (w.LEGehaltRezept.text() == "") or (w.LEFlaschenvolumen.text() == ""):
        print("Eine der Eingaben ist leer!")
        standartbox("Eine der Eingaben ist leer!")
    else:
        if Zutatentest == 0:
            try:
                int(w.LEGehaltRezept.text())
                int(w.LEFlaschenvolumen.text())
                if int(w.LEGehaltRezept.text()) <= 100:
                    c.execute("INSERT OR IGNORE INTO Zutaten(Name,Alkoholgehalt,Flaschenvolumen,Verbrauchsmenge,Verbrauch) VALUES (?,?,?,0,0)", (
                        w.LEZutatRezept.text(), int(w.LEGehaltRezept.text()), int(w.LEFlaschenvolumen.text())))
                    DB.commit()
                    w.LWZutaten.addItem(w.LEZutatRezept.text())
                    w.LEZutatRezept.clear()
                    w.LEGehaltRezept.clear()
                    w.LEFlaschenvolumen.clear()
                    # Zutaten_a()
                    ZutatenCB_Rezepte(w, DB, c)
                    ZutatenCB_Belegung(w, DB, c)
                    # Belegung_einlesen(w, DB, c)
                    print("Zutat eingetragen")
                    standartbox("Zutat eingetragen")
                else:
                    print("Alkoholgehalt kann nicht größer als 100 sein!")
                    standartbox(
                        "Alkoholgehalt kann nicht größer als 100 sein!")
            except ValueError:
                print("Alkoholgehalt und Flaschenvolumen muss eine Zahl sein!")
                standartbox(
                    "Alkoholgehalt und Flaschenvolumen muss eine Zahl sein!")
        else:
            print("Dieser Name existiert schon in der Datenbank!")
            standartbox("Dieser Name existiert schon in der Datenbank!")


def Zutaten_a(w, DB, c):
    """ Load all incredientnames into the ListWidget """
    w.LWZutaten.clear()
    Zspeicher = c.execute("SELECT Name FROM Zutaten")
    for Werte in Zspeicher:
        w.LWZutaten.addItem(Werte[0])


def Zutaten_delete(w, DB, c):
    """ Deletes an incredient out of the DB if its not needed in any recipe. \n
    In addition to do so, a password is needed in the interface.
    """
    ZID = 0
    if w.LEpw2.text() == globals.masterpassword:
        if not w.LWZutaten.selectedItems():
            print("Keine Zutat ausgewählt!")
            standartbox("Keine Zutat ausgewählt!")
        else:
            Zname = w.LWZutaten.currentItem().text()
            Zspeicher = c.execute(
                "SELECT ID FROM Zutaten WHERE Name = ?", (Zname,))
            for row in Zspeicher:
                ZID = row[0]
            # print(ZID)
            c.execute("SELECT COUNT(*) FROM Zusammen WHERE Zutaten_ID=?", (ZID,))
            Zutatentest = c.fetchone()[0]
            if Zutatentest == 0:
                c.execute("SELECT COUNT(*) FROM Belegung WHERE ID=?", (ZID,))
                Zutatentest = c.fetchone()[0]
                if Zutatentest == 0:
                    c.execute("DELETE FROM Zutaten WHERE ID = ?", (ZID,))
                    DB.commit()
                    ZutatenCB_Rezepte(w, DB, c)
                    ZutatenCB_Belegung(w, DB, c)
                    Zutaten_clear(w, DB, c)
                    Zutaten_a(w, DB, c)
                    # ich glaube die zeile hier ist unnötig
                    # Belegung_einlesen(w, DB, c)
                    print("Zutat mit der ID: <" + str(ZID) +
                          "> und dem Namen: <" + Zname + "> gelöscht!")
                    standartbox("Zutat mit der ID: <" + str(ZID) +
                                "> und dem Namen: <" + Zname + "> gelöscht!")
                else:
                    print("Achtung, die Zutat ist noch in der Belegung registriert!")
                    standartbox(
                        "Achtung, die Zutat ist noch in der Belegung registriert!")
            else:
                print("Zutat kann nicht gelöscht werden, da sie in " +
                      str(Zutatentest) + " Rezept(en) genutzt wird!")
                standartbox("Zutat kann nicht gelöscht werden, da sie in " +
                            str(Zutatentest) + " Rezept(en) genutzt wird!")
    else:
        print("Falsches Passwort!")
        standartbox("Falsches Passwort!")

    w.LEpw2.setText("")


def Zutaten_Zutaten_click(w, DB, c):
    """ Search the DB entry for the incredient and displays them """
    if w.LWZutaten.selectedItems():
        Zspeicher = c.execute(
            "SELECT Alkoholgehalt, Flaschenvolumen FROM Zutaten WHERE Name = ?", (w.LWZutaten.currentItem().text(),))
        for row in Zspeicher:
            w.LEGehaltRezept.setText(str(row[0]))
            w.LEFlaschenvolumen.setText(str(row[1]))
        w.LEZutatRezept.setText(w.LWZutaten.currentItem().text())


def Zutaten_aktualiesieren(w, DB, c):
    """ Update the selected incredient if all values are given and excact """
    ZID = 0
    if (w.LEZutatRezept.text() == "") or (w.LEGehaltRezept.text() == "") or (w.LEFlaschenvolumen.text() == ""):
        print("Eine der Eingaben ist leer!")
        standartbox("Eine der Eingaben ist leer!")
    else:
        try:
            int(w.LEGehaltRezept.text())
            int(w.LEFlaschenvolumen.text())
            if int(w.LEGehaltRezept.text()) <= 100:
                altername = w.LWZutaten.currentItem().text()
                neuerName = w.LEZutatRezept.text()
                Zspeicher = c.execute(
                    "SELECT ID FROM Zutaten WHERE Name = ?", (altername,))
                for row in Zspeicher:
                    ZID = int(row[0])
                # print(neuerName,int(w.LEGehaltRezept.text()),ZID)
                c.execute("UPDATE OR IGNORE Zutaten SET Name = ?, Alkoholgehalt = ?, Flaschenvolumen = ? WHERE ID = ?",
                          (neuerName, int(w.LEGehaltRezept.text()), int(w.LEFlaschenvolumen.text()), int(ZID)))
                DB.commit()
                w.LEZutatRezept.clear()
                w.LEGehaltRezept.clear()
                w.LEFlaschenvolumen.clear()
                Zutaten_a(w, DB, c)
                ZutatenCB_Rezepte(w, DB, c)
                ZutatenCB_Belegung(w, DB, c)
                Belegung_einlesen(w, DB, c)
                Belegung_progressbar(w, DB, c)
                print("Zutat aktualisiert")
                standartbox("Zutat aktualisiert")
            else:
                print(
                    "Alkoholgehalt und Flaschenvolumen kann nicht größer als 100 sein!")
                standartbox(
                    "Alkoholgehalt und Flaschenvolumen kann nicht größer als 100 sein!")
        except ValueError:
            print("Alkoholgehalt muss eine Zahl sein!")
            standartbox("Alkoholgehalt muss eine Zahl sein!")


def Zutaten_Flvolumen_pm(w, DB, c, operator):
    """ Increase or decrease the Bottlevolume by a given amount (25). \n
    The value cannot exceed the minimal or maximal Volume (100/1500).
    """
    minimalvolumen = 100
    maximalvolumen = 1500
    if w.LEFlaschenvolumen.text() == "":
        if operator == "+":
            w.LEFlaschenvolumen.setText(str(minimalvolumen))
    elif int(w.LEFlaschenvolumen.text()) <= minimalvolumen:
        if operator == "+":
            w.LEFlaschenvolumen.setText(
                str(int(w.LEFlaschenvolumen.text()) + 25))
    elif int(w.LEFlaschenvolumen.text()) >= maximalvolumen:
        if operator == "-":
            w.LEFlaschenvolumen.setText(
                str(int(w.LEFlaschenvolumen.text()) - 25))
    else:
        if operator == "+":
            w.LEFlaschenvolumen.setText(
                str(int(w.LEFlaschenvolumen.text()) + 25))
        else:
            w.LEFlaschenvolumen.setText(
                str(int(w.LEFlaschenvolumen.text()) - 25))


def Zutaten_clear(w, DB, c):
    """ Clears all entries in the incredient windoes """
    w.LWZutaten.clearSelection()
    w.LEZutatRezept.clear()
    w.LEGehaltRezept.clear()
    w.LEFlaschenvolumen.clear()


def save_Zutaten(w, DB, c):
    if w.LEpw2.text() == globals.masterpassword:
        with open('Zutaten_export.csv', mode='a', newline='') as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=',')
            csv_writer.writerow(
                ["----- Neuer Export von %s -----" % datetime.date.today()])
            row1 = []
            row2 = []
            Zspeicher = c.execute(
                "SELECT Name, Verbrauch FROM Zutaten ORDER BY Verbrauch DESC, Name ASC")
            for row in Zspeicher:
                row1.append(row[0])
                row2.append(row[1])
            csv_writer.writerow(row1)
            csv_writer.writerow(row2)
            csv_writer.writerow(["----- Gesamte Mengen über Lebenszeit -----"])
            row1 = []
            row2 = []
            Zspeicher = c.execute(
                "SELECT Name, Verbrauchsmenge FROM Zutaten ORDER BY Verbrauchsmenge DESC, Name ASC")
            for row in Zspeicher:
                row1.append(row[0])
                row2.append(row[1])
            csv_writer.writerow(row1)
            csv_writer.writerow(row2)
            csv_writer.writerow([" "])
        c.execute("UPDATE OR IGNORE Zutaten SET Verbrauch = 0")
        DB.commit()
        standartbox(
            "Alle Daten wurden exportiert und die zurücksetzbaren Zutatenmengen zurückgesetzt!")
    else:
        print("Falsches Passwort!")
        standartbox("Falsches Passwort!")
    w.LEpw2.clear()
