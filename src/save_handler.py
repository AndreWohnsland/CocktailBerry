import os
import datetime
import csv
from typing import List

from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.service_handler import SERVICE_HANDLER

DIRPATH = os.path.dirname(os.path.abspath(__file__))
logger = LoggerHandler("save_handler", "production_logs")


class SaveHandler:
    def export_ingredients(self, w):
        """Export the ingredients to a csv file, resets consumption"""
        if not DP_CONTROLLER.check_ingredient_password(w):
            DP_CONTROLLER.say_wrong_password()
            return
        consumption_list = DB_COMMANDER.get_consumption_data_lists_ingredients()
        self.save_quant("Zutaten_export.csv", consumption_list)
        DB_COMMANDER.delete_consumption_ingredients()
        logger.log_event("INFO", "Ingredient data was exported")

    def export_recipes(self, w):
        """Export the recipes to a csv file, resets count"""
        if not DP_CONTROLLER.check_recipe_password(w):
            DP_CONTROLLER.say_wrong_password()
            return
        consumption_list = DB_COMMANDER.get_consumption_data_lists_recipes()
        self.save_quant("Rezepte_export.csv", consumption_list)
        DB_COMMANDER.delete_consumption_recipes()
        logger.log_event("INFO", "Recipe data was exported")

    def save_quant(self, filename: str, data: List):
        """ Saves all the amounts of the ingredients/recipes to a csv and reset the counter to zero"""
        self.write_rows_to_csv(filename, [*data, [" "]])
        DP_CONTROLLER.say_all_data_exported()

    def write_rows_to_csv(self, filename: str, data_rows: List):
        """Write the data to the csv file, activate servicehandler for mail"""
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
            SERVICE_HANDLER.send_mail(full_file_name, read_file)


SAVE_HANDLER = SaveHandler()
