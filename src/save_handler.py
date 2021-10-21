import os
import datetime
import csv

from src.database_commander import DatabaseCommander
from src.display_handler import DisplayHandler
from src.display_controller import DisplayController
from src.service_handler import ServiceHandler

DB_COMMANDER = DatabaseCommander()
DP_HANDLER = DisplayHandler()
DP_CONTROLLER = DisplayController()
S_HANDLER = ServiceHandler()

DIRPATH = os.path.dirname(__file__)


class SaveHandler:
    def export_ingredients(self, w):
        consumption_list = DB_COMMANDER.get_consumption_data_lists_ingredients()
        successfull = self.save_quant(w.LEpw2, "Zutaten_export.csv", consumption_list)
        if not successfull:
            return
        DB_COMMANDER.delete_consumption_ingredients()

    def export_recipes(self, w):
        consumption_list = DB_COMMANDER.get_consumption_data_lists_recipes()
        successfull = self.save_quant(w.LEpw, "Rezepte_export.csv", consumption_list)
        if not successfull:
            return
        DB_COMMANDER.delete_consumption_recipes()

    def save_quant(self, line_edit_password, filename, data):
        """ Saves all the amounts of the ingredients/recipes to a csv and reset the counter to zero"""
        if not DP_CONTROLLER.check_password(line_edit_password):
            DP_HANDLER.standard_box("Falsches Passwort!")
            return False

        self.write_rows_to_csv(filename, [*data, [" "]])
        DP_HANDLER.standard_box("Alle Daten wurden exportiert und die zurücksetzbaren Mengen zurückgesetzt!")
        return True

    def write_rows_to_csv(self, filename, data_rows):
        dtime = str(datetime.date.today())
        dtime = dtime.replace("-", "")
        subfoldername = "saves"
        full_file_name = f"{dtime}_{filename}"
        savepath = os.path.join(DIRPATH, "..", subfoldername, full_file_name)
        with open(savepath, mode="a", newline="", encoding="utf-8") as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=",")
            for row in data_rows:
                csv_writer.writerow(row)
        with open(savepath, "rb") as read_file:
            S_HANDLER.send_mail(full_file_name, read_file)
