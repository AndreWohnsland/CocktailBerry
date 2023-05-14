import csv
from pathlib import Path
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QProgressBar
from PyQt5.QtCore import QSize

from src.database_commander import DB_COMMANDER
from src.filepath import SAVE_FOLDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.save_handler import SAVE_HANDLER
from src.ui.creation_utils import create_label
from src.ui_elements import Ui_DataWindow


class DataWindow(QMainWindow, Ui_DataWindow):
    """Creates the log window Widget."""

    def __init__(self):
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)
        self.button_reset.clicked.connect(self._export_and_recalculate)
        self.selection_data.activated.connect(self._display_data)

        self.since_reset_str = UI_LANGUAGE.get_translation("since_reset", "data_window")
        self.all_time_str = UI_LANGUAGE.get_translation("all_time", "data_window")
        self.grid = None

        self._populate_data()
        self._plot_data(
            self.local_data[self.since_reset_str],
            self.local_data_ingredients[self.since_reset_str]
        )

        UI_LANGUAGE.adjust_data_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _populate_data(self):
        """Gets data from files and db, assigns objects and fill dropdown"""
        self.data_files = self._get_saved_data_files()
        self.data_files_ingredients = self._get_saved_data_files("Ingredient")
        self.local_data = self._get_recipe_data()
        self.local_data_ingredients = self._get_ingredient_data()

        # generates the dropdown with options
        drop_down_options = [self.since_reset_str, self.all_time_str] + self.data_files
        DP_CONTROLLER.fill_single_combobox(self.selection_data, drop_down_options, clear_first=True, first_empty=False)

    def _export_and_recalculate(self):
        """Exports the data and recalculates the dropdowns / plot"""
        if not SAVE_HANDLER.export_data():
            return
        current_selection = self.selection_data.currentText()
        self._populate_data()
        DP_CONTROLLER.set_combobox_item(self.selection_data, current_selection)
        ingredient_data = self._get_ingredient_by_key(current_selection)
        self._plot_data(self.local_data[current_selection], ingredient_data)

    def _get_saved_data_files(self, pattern: str = "Recipe"):
        """Checks the logs folder for all existing log files"""
        return [file.name for file in SAVE_FOLDER.glob(f"*{pattern}*.csv")]

    def _display_data(self):
        selection = self.selection_data.currentText()
        data = self.local_data[selection]
        ingredient_data = self._get_ingredient_by_key(selection)
        self._plot_data(data, ingredient_data)

    def _get_ingredient_by_key(self, key: str):
        """Gets ingredient by the selection recipe data key.
        Schema is identical, need to replace Recipe with Ingredient"""
        return self.local_data_ingredients[
            key.replace("_Recipe_", "_Ingredient_")
        ]

    def _read_csv_file(self, to_read: Path):
        """Read and extracts the given csv file"""
        data = []
        with to_read.open(encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            for row in reader:
                data.append(row)
        return self._extract_data(data)

    def _get_recipe_data(self):
        """Gets the data from the database and the files"""
        data = DB_COMMANDER.get_consumption_data_lists_recipes()
        data = self._extract_data(data)
        for file in self.data_files:
            data[file] = self._read_csv_file(SAVE_FOLDER / file)[self.since_reset_str]
        return data

    def _get_ingredient_data(self):
        """Gets the data from the database and the files"""
        data = DB_COMMANDER.get_consumption_data_lists_ingredients()
        data = self._extract_data(data)
        for file in self.data_files_ingredients:
            data[file] = self._read_csv_file(SAVE_FOLDER / file)[self.since_reset_str]
        return data

    def _extract_data(self, data: list[list]):
        """Extracts the needed data from the exported data"""
        # The data has three rows:
        # first is the Names, with the first column being the date
        names = data[0][1::]
        # second is resettable data
        # data comes from csv, so it is str, need to convert to int
        since_reset = data[1][1::]
        since_reset = [int(x) for x in since_reset]
        # third is life time data
        all_time = data[2][1::]
        all_time = [int(x) for x in all_time]

        # Extract both into a dict containing name: quant
        # using only quantities greater than zero
        extracted = {}
        extracted[self.all_time_str] = {x: y for x, y in zip(names, all_time) if y > 0}
        extracted[self.since_reset_str] = {x: y for x, y in zip(names, since_reset) if y > 0}
        return extracted

    def _plot_data(self, data: dict, ingredient_data: dict):
        """Plots the given data in a barplot"""
        # first need to sort, then extract list of names / values
        names, values = self._sort_extract_data(data)

        self._clear_data()
        cocktail_label = UI_LANGUAGE.get_translation("cocktails_made", "data_window")
        self.label_made_cocktails.setText(cocktail_label + str(sum(values)))
        # regenerates the grid layout
        self.grid = QGridLayout()
        self.content_container.addLayout(self.grid)
        # if there is no data, skip
        if not data:
            return

        # first generate for recipe
        self._generate_bar_chart(names, values)
        # then generate for ingredients
        # need to calculate starting row
        start_row = len(values)
        names, values = self._sort_extract_data(ingredient_data)
        label = UI_LANGUAGE.get_translation("ingredient_volume", "data_window")
        ingredient_label = f"{label}{sum(values) / 1000:.2f} l"
        # add empty line to get some space
        spacer_label = create_label("", 12)
        spacer_label.setMaximumSize(QSize(16777215, 30))
        self.grid.addWidget(spacer_label, start_row, 0, 1, 1)
        ingredient_header = create_label(ingredient_label, 20, True, True, "header-underline")
        ingredient_header.setMaximumSize(QSize(16777215, 40))
        self.grid.addWidget(ingredient_header, start_row + 1, 0, 1, 3)
        self._generate_bar_chart(names, values, start_row + 2, " ml")

    def _sort_extract_data(self, data: dict):
        sorted_data = dict(sorted(data.items(), key=lambda i: -i[1]))
        names = list(sorted_data.keys())
        values = list(sorted_data.values())
        return names, values

    def _generate_bar_chart(self, names: list, values: list, start_row: int = 0, quantifier: str = "x"):
        """Generates one bar in the grid"""
        if self.grid is None:
            return
        for i, (name, value) in enumerate(zip(names, values), start_row):
            self.grid.addWidget(create_label(f"{name} ", 20, False, True), i, 0, 1, 1)
            self.grid.addWidget(create_label(f" ({value}{quantifier}) ", 20, True, True, "secondary"), i, 1, 1, 1)
            displayed_bar = QProgressBar(self)
            displayed_bar.setTextVisible(False)
            displayed_bar.setProperty("cssClass", "no-bg")
            displayed_bar.setValue(int(100 * value / max(values)))
            self.grid.addWidget(displayed_bar, i, 2, 1, 1)

    def _clear_data(self):
        """Removes data from the grid layout"""
        if self.grid is None:
            return
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            self.grid.removeWidget(widget)
        self.grid.deleteLater()
