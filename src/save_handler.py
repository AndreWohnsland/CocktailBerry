import datetime
import csv
from typing import List

from src.filepath import SAVE_FOLDER
from src.database_commander import DB_COMMANDER
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler

_logger = LoggerHandler("save_handler")


class SaveHandler:
    def export_data(self):
        """Export the ingredient and recipe data to two separate csvs, resets consumption."""
        if not DP_CONTROLLER.ask_to_export_data():
            return False
        self._export_ingredients()
        self._export_recipes()
        self._export_cost()
        DP_CONTROLLER.say_all_data_exported(str(SAVE_FOLDER))
        return True

    def _export_ingredients(self):
        """Export the ingredients to a csv file, resets consumption"""
        consumption_list = DB_COMMANDER.get_consumption_data_lists_ingredients()
        self._write_rows_to_csv("Ingredient_export", [*consumption_list, [" "]])
        DB_COMMANDER.delete_consumption_ingredients()
        _logger.log_event("INFO", "Ingredient data was exported")

    def _export_recipes(self):
        """Export the recipes to a csv file, resets count"""
        consumption_list = DB_COMMANDER.get_consumption_data_lists_recipes()
        self._write_rows_to_csv("Recipe_export", [*consumption_list, [" "]])
        DB_COMMANDER.delete_consumption_recipes()
        _logger.log_event("INFO", "Recipe data was exported")

    def _export_cost(self):
        """Export the cost to a csv file, this does not need resetting"""
        cost_list = DB_COMMANDER.get_cost_data_lists_ingredients()
        self._write_rows_to_csv("Cost_export", [*cost_list, [" "]])

    def _write_rows_to_csv(self, filename: str, data_rows: List):
        """Write the data to the csv file, activate service handler for mail"""
        dtime = datetime.datetime.now()
        prefix = dtime.strftime("%Y%m%d")
        # also build time suffix, in case user does double save
        suffix = dtime.strftime("%H%M%S")
        full_file_name = f"{prefix}_{filename}-{suffix}.csv"
        save_path = SAVE_FOLDER / full_file_name
        with open(save_path, mode="a", newline="", encoding="utf-8") as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=",")
            for row in data_rows:
                csv_writer.writerow(row)


SAVE_HANDLER = SaveHandler()
