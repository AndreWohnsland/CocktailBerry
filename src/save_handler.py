import os
import logging
import time
import datetime
import csv
from pathlib import Path

from src.database_commander import DatabaseCommander
from src.display_handler import DisplayHandler
from src.display_controler import DisplayControler

database_commander = DatabaseCommander()
display_handler = DisplayHandler()
display_controler = DisplayControler()


dirpath = os.path.dirname(__file__)


class SaveHandler:
    def export_ingredients(self, w):
        consumption_list = database_commander.get_consumption_data_lists_ingredients()
        successfull = self.save_quant(w.LEpw2, "Zutaten_export.csv", consumption_list)
        if not successfull:
            return
        database_commander.delete_consumption_ingredients()

    def export_recipes(self, w):
        consumption_list = database_commander.get_consumption_data_lists_recipes()
        successfull = self.save_quant(w.LEpw, "Rezepte_export.csv", consumption_list)
        if not successfull:
            return
        database_commander.delete_consumption_recipes()

    def save_quant(self, line_edit_password, filename, data):
        """ Saves all the amounts of the ingredients/recipes to a csv and reset the counter to zero"""
        if not display_controler.check_password(line_edit_password):
            display_handler.standard_box("Falsches Passwort!")
            return False

        self.write_rows_to_csv(filename, [*data, [" "]])
        display_handler.standard_box("Alle Daten wurden exportiert und die zurücksetzbaren Mengen zurückgesetzt!")
        return True

    def write_rows_to_csv(self, filename, data_rows):
        dtime = str(datetime.date.today())
        dtime = dtime.replace("-", "")
        subfoldername = "saves"
        savepath = os.path.join(dirpath, "..", subfoldername, f"{dtime}_{filename}")
        with open(savepath, mode="a", newline="") as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=",")
            for row in data_rows:
                csv_writer.writerow(row)
