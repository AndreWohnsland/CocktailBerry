from typing import TYPE_CHECKING

from PyQt5.QtCore import QDate, QTime
from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.datepicker import Ui_Datepicker
from src.utils import set_system_datetime

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class DatePicker(QMainWindow, Ui_Datepicker):
    """Creates the Window for the user to change date and time."""

    def __init__(self, parent: "MainScreen") -> None:
        """Set up the datepicker window."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # connects all the buttons
        self.pb_ok.clicked.connect(self._ok_clicked)
        self.mainscreen = parent
        self._init_date_and_time()
        UI_LANGUAGE.adjust_datepicker_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _ok_clicked(self) -> None:
        """Submit the selected Time in the interface to the OS."""
        d: QDate = self.selected_date.date()  # pylint: disable=invalid-name
        t: QTime = self.selected_time.time()  # pylint: disable=invalid-name
        # Need the format = timedatectl set-time YYYY-MM-DD HH:MM:SS
        datetime_string = f"{d.year()}-{d.month():02}-{d.day():02} {t.hour():02}:{t.minute():02}:00"
        set_system_datetime(datetime_string)
        self.close()

    def _init_date_and_time(self) -> None:
        self.selected_time.setTime(QTime.currentTime())
        self.selected_date.setDate(QDate.currentDate())
