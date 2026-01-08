from __future__ import annotations

from PyQt6.QtWidgets import QGridLayout, QMainWindow

from src.data_utils import ALL_TIME, SINCE_RESET, generate_consume_data
from src.database_commander import DB_COMMANDER as DBC
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.models import ConsumeData
from src.save_handler import SAVE_HANDLER
from src.ui.creation_utils import RowCounter, add_grid_header, add_grid_spacer, generate_grid_bar_chart
from src.ui_elements import Ui_DataWindow


class DataWindow(QMainWindow, Ui_DataWindow):
    """Creates the log window Widget."""

    def __init__(self) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)
        self.button_reset.clicked.connect(self._export_and_recalculate)
        self.selection_data.activated.connect(self._display_data)

        self.grid: QGridLayout | None = None
        self.row_counter = RowCounter(0)

        self.consume_data: dict[str, ConsumeData] = {}
        self._populate_data()
        self._plot_data(self.consume_data[SINCE_RESET])

        UI_LANGUAGE.adjust_data_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _populate_data(self) -> None:
        """Get data from files and db, assigns objects and fill dropdown."""
        self.consume_data = generate_consume_data()
        # generates the dropdown with options
        dates = DBC.get_export_dates()
        drop_down_options = [SINCE_RESET, ALL_TIME, *dates]
        DP_CONTROLLER.fill_single_combobox(self.selection_data, drop_down_options, clear_first=True, first_empty=False)

    def _export_and_recalculate(self) -> None:
        """Export the data and recalculates the dropdowns / plot."""
        if not DP_CONTROLLER.ask_to_export_data():
            return
        SAVE_HANDLER.export_data()
        DP_CONTROLLER.say_all_data_exported()
        current_selection = self.selection_data.currentText()
        self._populate_data()
        DP_CONTROLLER.set_combobox_item(self.selection_data, current_selection)
        self._plot_data(self.consume_data[current_selection])

    def _display_data(self) -> None:
        selection = self.selection_data.currentText()
        self._plot_data(self.consume_data[selection])

    def _plot_data(self, consume_data: ConsumeData) -> None:
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
        self.row_counter = RowCounter(0)
        # if there is no recipe_data, skip
        if not recipe_data:
            return

        # first generate chart for recipe
        generate_grid_bar_chart(self, self.grid, self.row_counter, names, values)
        # generate data for ingredients
        names, values = self._sort_extract_data(ingredient_data)
        label = UI_LANGUAGE.get_translation("ingredient_volume", "data_window")
        ingredient_label = f"{label}{sum(values) / 1000:.2f} l"
        # add empty line to get some space
        add_grid_spacer(self.grid, self.row_counter)
        add_grid_header(self.grid, self.row_counter, ingredient_label)
        generate_grid_bar_chart(self, self.grid, self.row_counter, names, values, " ml")
        # generate cost at the end
        add_grid_spacer(self.grid, self.row_counter)
        cost_label = UI_LANGUAGE.get_translation("no_cost_data", "data_window")
        if cost_data is not None:
            total_cost = sum(cost_data.values())
            cost_label = UI_LANGUAGE.get_translation("cost_ingredients", "data_window")
            cost_label = f"{cost_label}{total_cost / 100:.2f}"
        add_grid_header(self.grid, self.row_counter, cost_label)
        # we stop here if there is no cost data
        if cost_data is None:
            return
        names, values = self._sort_extract_data(cost_data)
        # need to convert values from cent or similar to euro
        relative_values = [x / 100 for x in values]
        generate_grid_bar_chart(self, self.grid, self.row_counter, names, relative_values, "")

    def _sort_extract_data(self, data: dict[str, int]) -> tuple[list[str], list[int]]:
        sorted_data = dict(sorted(data.items(), key=lambda i: -i[1]))
        names = list(sorted_data.keys())
        values = list(sorted_data.values())
        return names, values

    def _clear_data(self) -> None:
        """Remove data from the grid layout."""
        self.row_counter = RowCounter(0)
        if self.grid is None:
            return
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            self.grid.removeWidget(widget)
        self.grid.deleteLater()
