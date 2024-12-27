import csv
import datetime

from src.database_commander import DatabaseCommander
from src.filepath import SAVE_FOLDER
from src.logger_handler import LoggerHandler

_logger = LoggerHandler("save_handler")


class SaveHandler:
    def export_data(self):
        """Export the ingredient and recipe data to two separate csvs, resets consumption."""
        # need to do cost first, since consumption is reset after other exports
        self._export_cost()
        self._export_ingredients()
        self._export_recipes()

    def _export_ingredients(self):
        """Export the ingredients to a csv file, resets consumption."""
        DBC = DatabaseCommander()
        consumption_list = DBC.get_consumption_data_lists_ingredients()
        self._write_rows_to_csv("Ingredient_export", [*consumption_list, [" "]])
        DBC.delete_consumption_ingredients()
        _logger.log_event("INFO", "Ingredient data was exported")

    def _export_recipes(self):
        """Export the recipes to a csv file, resets count."""
        DBC = DatabaseCommander()
        consumption_list = DBC.get_consumption_data_lists_recipes()
        self._write_rows_to_csv("Recipe_export", [*consumption_list, [" "]])
        DBC.delete_consumption_recipes()
        _logger.log_event("INFO", "Recipe data was exported")

    def _export_cost(self):
        """Export the cost to a csv file, this does not need resetting."""
        DBC = DatabaseCommander()
        cost_list = DBC.get_cost_data_lists_ingredients()
        self._write_rows_to_csv("Cost_export", [*cost_list, [" "]])

    def _write_rows_to_csv(self, filename: str, data_rows: list):
        """Write the data to the csv file, activate service handler for mail."""
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
