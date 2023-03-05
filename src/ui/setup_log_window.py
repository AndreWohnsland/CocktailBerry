from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.logwindow import Ui_LogWindow

_DIRPATH = Path(__file__).parent.absolute()
_LOG_FOLDER = _DIRPATH.parents[1] / "logs"
_DEFAULT_SELECTED = "production_logs.log"


class LogWindow(QMainWindow, Ui_LogWindow):
    """ Creates the log window Widget. """

    def __init__(self):
        """ Init. Connect all the buttons and set window policy. """
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)

        # Get log file names, fill widget, select default, if it exists
        self.log_files = self._get_log_files()
        self.selection_logs.activated.connect(self._read_logs)
        DP_CONTROLLER.fill_single_combobox(self.selection_logs, self.log_files, first_empty=False)
        if _DEFAULT_SELECTED in self.log_files:
            DP_CONTROLLER.set_combobox_item(self.selection_logs, _DEFAULT_SELECTED)
        # activated does only trigger if changed by user, so we need to read in here
        self._read_logs()

        self.move(0, 0)
        UI_LANGUAGE.adjust_log_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _get_log_files(self):
        """Checks the logs folder for all existing log files"""
        return [file.name for file in _LOG_FOLDER.glob("*.log")]

    def _read_logs(self):
        """Read the current selected log file"""
        log_name = self.selection_logs.currentText()
        # Return if empty selection
        if log_name == "":
            return
        log_path = _LOG_FOLDER / log_name
        log_text = log_path.read_text()
        latest_to_oldest = "\n".join(log_text.splitlines()[::-1])
        self.text_display.setText(latest_to_oldest)
