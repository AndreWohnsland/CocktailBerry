""" Creates the single Tables and Unique indexes For an new Database, and also the Numbering of the Bottles.
This is only needed when there is no Database (due to deleting it or simply not having any).
"""
import sqlite3
from loggerconfig import logfunction


@logfunction
def create_new_db(DB, c):
    """ Creates the new DB and the Tables: 'Rezepte', 'Zutaten', 'Zusammen' and 'Belegung'
    as well as their needed properties.
    """
    # Creates each Table
    c.execute("CREATE TABLE IF NOT EXISTS Rezepte(ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, Name TEXT NOT NULL, Alkoholgehalt INTEGER NOT NULL, Menge INTEGER NOT NULL, Kommentar TEXT, Anzahl_Lifetime INTEGER, Anzahl INTEGER, Enabled INTEGER, V_Alk INTEGER, c_Alk INTEGER, V_Com INTEGER, c_Com INTEGER);")
    c.execute("CREATE TABLE IF NOT EXISTS Zutaten(ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, Name TEXT NOT NULL, Alkoholgehalt INTEGER NOT NULL, Flaschenvolumen INTEGER NOT NULL, Verbrauchsmenge INTEGER, Verbrauch INTEGER, Mengenlevel INTEGER, Hand INTEGER);")
    c.execute("CREATE TABLE IF NOT EXISTS Zusammen(Rezept_ID INTEGER NOT NULL, Zutaten_ID INTEGER NOT NULL, Menge INTEGER NOT NULL, Alkoholisch INTEGER NOT NULL, Hand INTEGER);")
    c.execute("CREATE TABLE IF NOT EXISTS Belegung(Flasche INTEGER NOT NULL, Zutat_F TEXT NOT NULL, ID INTEGER, Mengenlevel INTEGER);")
    c.execute("CREATE TABLE IF NOT EXISTS Vorhanden(ID INTEGER NOT NULL);")
    DB.commit()

    # Creating the Unique Indexes
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_zutaten_name ON Zutaten(Name)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_rezepte_name ON Rezepte(Name)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_flasche ON Belegung(Flasche)")
    DB.commit()

    # Creating the Space Naming of the Bottles
    for Flaschen_C in range(1, 13):
        c.execute("INSERT INTO Belegung(Flasche,Zutat_F) VALUES (?,?)",(Flaschen_C, ""))
    DB.commit()
