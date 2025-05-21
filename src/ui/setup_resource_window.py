from PyQt5.QtWidgets import QGridLayout, QMainWindow

from src.database_commander import DB_COMMANDER as DBC
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui.creation_utils import RowCounter, add_grid_header, add_grid_spacer, add_grid_text, generate_grid_bar_chart
from src.ui_elements import Ui_ResourceWindow


class ResourceWindow(QMainWindow, Ui_ResourceWindow):
    """Creates the resource Window."""

    def __init__(self) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)

        # limit the plot to x data points (will be aggregated in buckets)
        self.max_data_points = 15
        self.grid: QGridLayout | None = None
        self.row_counter = RowCounter(0)
        resource_info = DBC.get_resource_session_numbers()
        self.session_data = {f"{x.start_time} ({x.session_id})": x.session_id for x in resource_info}
        if self.session_data:
            DP_CONTROLLER.fill_single_combobox(
                self.selection_data,
                list(reversed(self.session_data.keys())),
                first_empty=False,
                sort_items=False,
            )
            self.selection_data.currentTextChanged.connect(self._select_resource_data)
            self._select_resource_data()

        UI_LANGUAGE.adjust_resource_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _select_resource_data(self) -> None:
        """Select the resource data from the database and fill the table."""
        self._clear_data()
        self.grid = QGridLayout()
        self.content_container.addLayout(self.grid)
        self.row_counter = RowCounter(0)
        data = DBC.get_resource_stats(self.session_data[self.selection_data.currentText()])
        add_grid_header(self.grid, self.row_counter, "RAM")
        add_grid_text(
            self.grid,
            self.row_counter,
            f"Mean: {data.mean_ram:.1f}%, Min: {data.min_ram:.1f}%, Max: {data.max_ram:.1f}%",
        )
        generate_grid_bar_chart(
            self,
            self.grid,
            self.row_counter,
            list(range(1, self.max_data_points + 1)),
            self._create_buckets(data.raw_ram, self.max_data_points),
            "%",
        )
        add_grid_spacer(self.grid, self.row_counter)
        add_grid_header(self.grid, self.row_counter, "CPU")
        add_grid_text(
            self.grid,
            self.row_counter,
            f"Mean: {data.mean_cpu:.1f}%, Min: {data.min_cpu:.1f}%, Max: {data.max_cpu:.1f}%",
        )
        generate_grid_bar_chart(
            self,
            self.grid,
            self.row_counter,
            list(range(1, self.max_data_points + 1)),
            self._create_buckets(data.raw_cpu, self.max_data_points),
            "%",
        )

    def _create_buckets(self, data: list[float], n: int) -> list[float]:
        """Create n buckets of the data."""
        if len(data) < n:
            return data
        bucket_size = len(data) // n
        buckets = [data[i : i + bucket_size] for i in range(0, len(data), bucket_size)]
        return [round(sum(x) / len(x), 1) for x in buckets]

    def _clear_data(self) -> None:
        """Remove data from the grid layout."""
        self.row_counter = RowCounter(0)
        if self.grid is None:
            return
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            self.grid.removeWidget(widget)
        self.grid.deleteLater()
