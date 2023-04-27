import csv
from pathlib import Path
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QProgressBar

from src.database_commander import DB_COMMANDER
from src.filepath import SAVE_FOLDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.save_handler import SAVE_HANDLER
from src.ui.creation_utils import create_label
from src.ui_elements import Ui_DataWindow


class DataWindow(QMainWindow, Ui_DataWindow):
    """ Creates the log window Widget. """

    def __init__(self):
        """ Init. Connect all the buttons and set window policy. """
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)
        self.button_reset.clicked.connect(SAVE_HANDLER.export_data)

        self.since_reset_str = UI_LANGUAGE.get_translation("since_reset", "data_window")
        self.all_time_str = UI_LANGUAGE.get_translation("all_time", "data_window")
        self.grid = None

        self.data_files = self._get_saved_data_files()
        self.selection_data.activated.connect(self._display_data)
        self.local_data = self._get_local_data()

        # generates the dropdown with options
        drop_down_options = [self.since_reset_str, self.all_time_str] + self.data_files
        DP_CONTROLLER.fill_single_combobox(self.selection_data, drop_down_options, first_empty=False)

        self._plot_data(self.local_data[self.since_reset_str])

        UI_LANGUAGE.adjust_data_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _get_saved_data_files(self):
        """Checks the logs folder for all existing log files"""
        return [file.name for file in SAVE_FOLDER.glob("*Recipe*.csv")]

    def _display_data(self):
        selection = self.selection_data.currentText()
        if selection == self.all_time_str:
            data = self.local_data[self.all_time_str]
        elif selection == self.since_reset_str:
            data = self.local_data[self.since_reset_str]
        else:
            data = self._read_csv_file(SAVE_FOLDER / selection)[self.since_reset_str]
        self._plot_data(data)

    def _read_csv_file(self, to_read: Path):
        """Read and extracts the given csv file"""
        data = []
        with to_read.open() as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            for row in reader:
                data.append(row)
        return self._extract_data(data)

    def _get_local_data(self):
        """Gets the data from the database"""
        data = DB_COMMANDER.get_consumption_data_lists_recipes()
        return self._extract_data(data)

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

    def _plot_data(self, data: dict):
        """Plots the given data in a barplot"""
        # first need to sort, then extract list of names / values
        sorted_data = dict(sorted(data.items(), key=lambda i: -i[1]))
        names = list(sorted_data.keys())
        values = list(sorted_data.values())

        self._clear_data()
        cocktail_label = UI_LANGUAGE.get_translation("cocktails_made", "data_window")
        self.label_made_cocktails.setText(cocktail_label + str(sum(values)))
        # regenerates the grid layout
        self.grid = QGridLayout()
        self.content_container.addLayout(self.grid)
        # generates the elements in the grid
        for i, (name, value) in enumerate(zip(names, values)):
            self.grid.addWidget(create_label(f"{name} ", 20, False, True), i, 0, 1, 1)
            self.grid.addWidget(create_label(f" ({value}x) ", 20, True, True, "secondary"), i, 1, 1, 1)
            displayed_bar = QProgressBar(self)
            displayed_bar.setTextVisible(False)
            displayed_bar.setProperty("cssClass", "no-bg")
            displayed_bar.setValue(int(100 * value / max(values)))
            self.grid.addWidget(displayed_bar, i, 3, 1, 1)

    def _clear_data(self):
        """Removes data from the grid layout"""
        if self.grid is None:
            return
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            self.grid.removeWidget(widget)
        self.grid.deleteLater()
