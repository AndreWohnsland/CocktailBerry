import sys
import sqlite3
import time
import datetime
import csv
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import globals
from msgboxgenerate import standartbox

from src.database_commander import DatabaseCommander
from src.display_handler import DisplayHandler
from src.display_controler import DisplayControler

database_commander = DatabaseCommander()
display_handler = DisplayHandler()
display_controler = DisplayControler()


def plusminus(label, operator, minimal=0, maximal=1000, dm=10):
    """ increases or decreases the value by a given amount in the boundaries"""
    try:
        value_ = int(label.text())
        value_ = value_ + (dm if operator == "+" else -dm)
        value_ = min(maximal, max(minimal, (value_ // dm) * dm))
    except ValueError:
        value_ = maximal if operator == "+" else minimal
    label.setText(str(value_))


def export_ingredients(w):
    consumption_list = database_commander.get_consumption_data_lists_ingredients()
    successfull = save_quant(w.LEpw2, "Zutaten_export.csv", consumption_list)
    if not successfull:
        return
    database_commander.delete_consumption_ingredients()


def export_recipes(w):
    consumption_list = database_commander.get_consumption_data_lists_recipes()
    successfull = save_quant(w.LEpw, "Rezepte_export.csv", consumption_list)
    if not successfull:
        return
    database_commander.delete_consumption_recipes()


def save_quant(line_edit_password, filename, data):
    """ Saves all the amounts of the ingredients/recipes to a csv and reset the counter to zero"""
    if not display_controler.check_password(line_edit_password):
        display_handler.standard_box("Falsches Passwort!")
        return False

    write_rows_to_csv(filename, [*data, [" "]])
    display_handler.standard_box("Alle Daten wurden exportiert und die zurücksetzbaren Mengen zurückgesetzt!")
    return True


def write_rows_to_csv(filename, data_rows):
    dtime = str(datetime.date.today())
    dtime = dtime.replace("-", "")
    dirpath = os.path.dirname(__file__)
    subfoldername = "saves"
    savepath = os.path.join(dirpath, subfoldername, f"{dtime}_{filename}")
    with open(savepath, mode="a", newline="") as writer_file:
        csv_writer = csv.writer(writer_file, delimiter=",")
        for row in data_rows:
            csv_writer.writerow(row)
