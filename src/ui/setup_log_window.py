from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LogFiles
from src.ui_elements.logwindow import Ui_LogWindow
from src.utils import read_log_file


class LogWindow(QMainWindow, Ui_LogWindow):
    """Creates the log window Widget."""

    def __init__(self) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)

        self.selection_logs.activated.connect(self._read_logs)
        self.check_warning.stateChanged.connect(self._read_logs)
        DP_CONTROLLER.fill_single_combobox(self.selection_logs, list(LogFiles), first_empty=False)
        DP_CONTROLLER.set_combobox_item(self.selection_logs, LogFiles.PRODUCTION)
        # activated does only trigger if changed by user, so we need to read in here
        self._read_logs()

        UI_LANGUAGE.adjust_log_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _read_logs(self) -> None:
        """Read the current selected log file."""
        log_file = LogFiles(self.selection_logs.currentText())
        min_level = "WARNING" if self.check_warning.isChecked() else "DEBUG"
        logs_to_render = "\n".join(read_log_file(log_file, min_level))
        self.text_display.setText(logs_to_render)
