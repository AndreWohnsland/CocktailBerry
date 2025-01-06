from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGridLayout, QMainWindow, QProgressBar

from src.data_utils import ALL_TIME, SINCE_RESET, ConsumeData, generate_consume_data, get_saved_dates
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.filepath import SAVE_FOLDER
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

        self.grid = None
        self.grid_current_row = 0

        self.consume_data: dict[str, ConsumeData] = {}
        self._populate_data()
        self._plot_data(self.consume_data[SINCE_RESET])

        UI_LANGUAGE.adjust_data_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _populate_data(self):
        """Get data from files and db, assigns objects and fill dropdown."""
        self.consume_data = generate_consume_data()
        # generates the dropdown with options
        dates = get_saved_dates()
        drop_down_options = [SINCE_RESET, ALL_TIME, *dates]
        DP_CONTROLLER.fill_single_combobox(self.selection_data, drop_down_options, clear_first=True, first_empty=False)

    def _export_and_recalculate(self):
        """Export the data and recalculates the dropdowns / plot."""
        if not DP_CONTROLLER.ask_to_export_data():
            return
        SAVE_HANDLER.export_data()
        DP_CONTROLLER.say_all_data_exported(str(SAVE_FOLDER))
        current_selection = self.selection_data.currentText()
        self._populate_data()
        DP_CONTROLLER.set_combobox_item(self.selection_data, current_selection)
        self._plot_data(self.consume_data[current_selection])

    def _get_saved_data_files(self, pattern: str = "Recipe"):
        """Check the logs folder for all existing log files."""
        return [file.name for file in SAVE_FOLDER.glob(f"*{pattern}*.csv")]

    def _display_data(self):
        selection = self.selection_data.currentText()
        self._plot_data(self.consume_data[selection])

    def _plot_data(self, consume_data: ConsumeData):
        """Plot the given data in a barplot."""
        # first need to sort, then extract list of names / values
        recipe_data = consume_data.recipes
        ingredient_data = consume_data.ingredients
        cost_data = consume_data.cost
        names, values = self._sort_extract_data(recipe_data)

        self._clear_data()
        cocktail_label = UI_LANGUAGE.get_translation("cocktails_made", "data_window")
        self.label_made_cocktails.setText(cocktail_label + str(sum(values)))
        # regenerates the grid layout
        self.grid = QGridLayout()
        self.content_container.addLayout(self.grid)
        # if there is no recipe_data, skip
        if not recipe_data:
            return

        # first generate chart for recipe
        self._generate_bar_chart(names, values)
        # generate data for ingredients
        names, values = self._sort_extract_data(ingredient_data)
        label = UI_LANGUAGE.get_translation("ingredient_volume", "data_window")
        ingredient_label = f"{label}{sum(values) / 1000:.2f} l"
        # add empty line to get some space
        self._add_spacer(self.grid_current_row)
        self._add_header(self.grid_current_row, ingredient_label)
        self._generate_bar_chart(names, values, self.grid_current_row, " ml")
        # generate cost at the end
        self._add_spacer(self.grid_current_row)
        cost_label = UI_LANGUAGE.get_translation("no_cost_data", "data_window")
        if cost_data is not None:
            total_cost = sum(cost_data.values())
            cost_label = UI_LANGUAGE.get_translation("cost_ingredients", "data_window")
            cost_label = f"{cost_label}{total_cost/100:.2f}"
        self._add_header(self.grid_current_row + 1, cost_label)
        # we stop here if there is no cost data
        if cost_data is None:
            return
        names, values = self._sort_extract_data(cost_data)
        # need to convert values from cent or similar to euro
        values = [x / 100 for x in values]
        self._generate_bar_chart(names, values, self.grid_current_row, "")

    def _add_spacer(self, row: int):
        """Add a spacer to the grid layout."""
        if self.grid is None:
            return
        spacer_label = create_label("", 12)
        spacer_label.setMaximumSize(QSize(16777215, 30))
        self.grid.addWidget(spacer_label, row, 0, 1, 1)
        self.grid_current_row += 1

    def _add_header(self, row: int, text: str):
        """Add a header to the grid layout."""
        if self.grid is None:
            return
        header_label = create_label(text, 20, True, True, css_class="header-underline", min_h=40, max_h=50)
        self.grid.addWidget(header_label, row, 0, 1, 3)
        self.grid_current_row += 2

    def _sort_extract_data(self, data: dict):
        sorted_data = dict(sorted(data.items(), key=lambda i: -i[1]))
        names = list(sorted_data.keys())
        values = list(sorted_data.values())
        return names, values

    def _generate_bar_chart(self, names: list, values: list, start_row: int = 0, quantifier: str = "x"):
        """Generate one bar in the grid."""
        if self.grid is None:
            return
        for i, (name, value) in enumerate(zip(names, values), start_row):
            self.grid.addWidget(create_label(f"{name} ", 20, False, True), i, 0, 1, 1)
            self.grid.addWidget(
                create_label(f" {value}{quantifier} ", 20, True, True, css_class="secondary"), i, 1, 1, 1
            )
            displayed_bar = QProgressBar(self)
            displayed_bar.setTextVisible(False)
            displayed_bar.setProperty("cssClass", "no-bg")
            displayed_bar.setValue(int(100 * value / max(values)))
            self.grid.addWidget(displayed_bar, i, 2, 1, 1)
            self.grid_current_row += 1

    def _clear_data(self):
        """Remove data from the grid layout."""
        self.grid_current_row = 0
        if self.grid is None:
            return
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            self.grid.removeWidget(widget)
        self.grid.deleteLater()
