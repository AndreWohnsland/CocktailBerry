import datetime
import csv
from pathlib import Path
from typing import List

from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler

_DIRPATH = Path(__file__).parent.absolute()
_logger = LoggerHandler("save_handler")


class SaveHandler:
    def export_ingredients(self):
        """Export the ingredients to a csv file, resets consumption"""
        if not DP_CONTROLLER.password_prompt():
            return
        consumption_list = DB_COMMANDER.get_consumption_data_lists_ingredients()
        self._save_quant("Ingredient_export.csv", consumption_list)
        DB_COMMANDER.delete_consumption_ingredients()
        _logger.log_event("INFO", "Ingredient data was exported")

    def export_recipes(self):
        """Export the recipes to a csv file, resets count"""
        if not DP_CONTROLLER.password_prompt():
            return
        consumption_list = DB_COMMANDER.get_consumption_data_lists_recipes()
        self._save_quant("Recipe_export.csv", consumption_list)
        DB_COMMANDER.delete_consumption_recipes()
        _logger.log_event("INFO", "Recipe data was exported")

    def _save_quant(self, filename: str, data: List):
        """ Saves all the amounts of the ingredients/recipes to a csv and reset the counter to zero"""
        self._write_rows_to_csv(filename, [*data, [" "]])
        DP_CONTROLLER.say_all_data_exported()

    def _write_rows_to_csv(self, filename: str, data_rows: List):
        """Write the data to the csv file, activate service handler for mail"""
        dtime = str(datetime.date.today())
        dtime = dtime.replace("-", "")
        subfolder_name = "saves"
        full_file_name = f"{dtime}_{filename}"
        save_path = _DIRPATH.parent / subfolder_name / full_file_name
        with open(save_path, mode="a", newline="", encoding="utf-8") as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=",")
            for row in data_rows:
                csv_writer.writerow(row)


SAVE_HANDLER = SaveHandler()
