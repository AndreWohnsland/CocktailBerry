from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.logwindow import Ui_LogWindow
from src.utils import get_log_files, read_log_file

_DEFAULT_SELECTED = "production_logs.log"


class LogWindow(QMainWindow, Ui_LogWindow):
    """Creates the log window Widget."""

    def __init__(self):
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)

        # Get log file names, fill widget, select default, if it exists
        self.log_files = get_log_files()
        self.selection_logs.activated.connect(self._read_logs)
        self.check_warning.stateChanged.connect(self._read_logs)
        DP_CONTROLLER.fill_single_combobox(self.selection_logs, self.log_files, first_empty=False)
        if _DEFAULT_SELECTED in self.log_files:
            DP_CONTROLLER.set_combobox_item(self.selection_logs, _DEFAULT_SELECTED)
        # activated does only trigger if changed by user, so we need to read in here
        self._read_logs()

        UI_LANGUAGE.adjust_log_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _read_logs(self):
        """Read the current selected log file."""
        log_name = self.selection_logs.currentText()
        # Return if empty selection
        if log_name == "":
            return
        warning_and_higher = self.check_warning.isChecked()
        logs_to_render = "\n".join(read_log_file(log_name, warning_and_higher))
        self.text_display.setText(logs_to_render)
