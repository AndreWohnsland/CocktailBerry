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


class LoggerHandler:
    """Handler Class for Generating Logger and Logging events"""

    log_folder = os.path.join(dirpath, "..", "logs")

    def __init__(self, loggername, filename, new_handler=False):
        self.path = os.path.join(LoggerHandler.log_folder, f"{filename}.log")
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M", filename=self.path, filemode="a",
        )
        self.logger = logging.getLogger(loggername)
        self.TEMPLATE = "{:-^80}"

    def log_event(self, level, message):
        self.logger.log(getattr(logging, level), message)

    def log_header(self, level, message):
        self.log_event(level, self.TEMPLATE.format(message,))

    def log_start_program(self):
        self.logger.info(self.TEMPLATE.format("Starting the Programm",))


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
        savepath = os.path.join(dirpath, subfoldername, f"{dtime}_{filename}")
        with open(savepath, mode="a", newline="") as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=",")
            for row in data_rows:
                csv_writer.writerow(row)


def plusminus(label, operator, minimal=0, maximal=1000, dm=10):
    """ increases or decreases the value by a given amount in the boundaries"""
    try:
        value_ = int(label.text())
        value_ = value_ + (dm if operator == "+" else -dm)
        value_ = min(maximal, max(minimal, (value_ // dm) * dm))
    except ValueError:
        value_ = maximal if operator == "+" else minimal
    label.setText(str(value_))


###### This are temporary Helper Functions, they will be moved later in the UI parent class / there will be objects for them
def generate_CBB_names(w):
    return [getattr(w, f"CBB{x}") for x in range(1, 11)]


def generate_CBR_names(w):
    return [getattr(w, f"CBR{x}") for x in range(1, 9)]


def generate_LBelegung_names(w):
    return [getattr(w, f"LBelegung{x}") for x in range(1, 11)]


def generate_PBneu_names(w):
    return [getattr(w, f"PBneu{x}") for x in range(1, 11)]


def generate_ProBBelegung_names(w):
    return [getattr(w, f"ProBBelegung{x}") for x in range(1, 11)]


def generate_ingredient_fields(w):
    return [[w.LEZutatRezept, w.LEGehaltRezept, w.LEFlaschenvolumen], w.CHBHand, w.LWZutaten]


def generate_maker_ingredients_fields(w):
    return [getattr(w, f"LZutat{x}") for x in range(1, 11)]


def generate_maker_volume_fields(w):
    return [getattr(w, f"LMZutat{x}") for x in range(1, 11)]
