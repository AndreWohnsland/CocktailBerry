import re
from collections import Counter
from PyQt5.QtWidgets import QMainWindow

from src.filepath import LOG_FOLDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.logwindow import Ui_LogWindow

_DEFAULT_SELECTED = "production_logs.log"
_DEBUG_FILE = "debuglog.log"


class LogWindow(QMainWindow, Ui_LogWindow):
    """ Creates the log window Widget. """

    def __init__(self):
        """ Init. Connect all the buttons and set window policy. """
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)

        # Get log file names, fill widget, select default, if it exists
        self.log_files = self._get_log_files()
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

    def _get_log_files(self):
        """Checks the logs folder for all existing log files"""
        return [file.name for file in LOG_FOLDER.glob("*.log")]

    def _read_logs(self):
        """Read the current selected log file"""
        log_name = self.selection_logs.currentText()
        # Return if empty selection
        if log_name == "":
            return
        log_path = LOG_FOLDER / log_name
        log_text = log_path.read_text()
        warning_and_higher = self.check_warning.isChecked()
        # Handle debug logs differently, since they save error traces,
        # just display the read in text from log in this case
        if log_name == _DEBUG_FILE:
            logs_to_render = self._parse_debug_logs(log_text)
        else:
            logs_to_render = self._parse_log(log_text, warning_and_higher)
        self.text_display.setText(logs_to_render)

    def _parse_log(self, log_text: str, warning_and_higher: bool):
        """Parse all logs and return display object.
        Needs logs from new to old, if same message was already there, skip it.
        """
        data: dict[str, str] = {}
        counter: Counter[str] = Counter()
        for line in log_text.splitlines()[::-1]:
            date, message = self._parse_log_line(line)
            if message not in data:
                data[message] = date
                counter[message] = 1
            else:
                counter[message] += 1
        log_list_data = [
            f"{key} ({counter[key]}x, latest: {value})" for key, value in data.items()
        ]
        # Filter out DEBUG or INFO msgs
        if warning_and_higher:
            accepted = ["WARNING", "ERROR", "CRITICAL"]
            log_list_data = [x for x in log_list_data if any(a in x for a in accepted)]
        return "\n".join(log_list_data)

    def _parse_log_line(self, line: str):
        """Parse the log message and return the timestamp + msg"""
        parts = line.split(" | ", maxsplit=1)
        parsed_date = parts[0]
        # usually, we only get 2 parts, due to the maxsplit
        parsed_message = " | ".join(parts[1::])
        return parsed_date, parsed_message

    def _parse_debug_logs(self, log):
        """Parses and inverts the debug logs"""
        # having into group returns also the matched date
        # This needs to be joined before inverting.
        # Also, the first value is an empty string
        date_regex = r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})"
        information_list = [x for x in re.split(date_regex, log) if x != ""]
        pairs = [" ".join(information_list[i:i + 2]) for i in range(0, len(information_list), 2)]
        return "\n".join(pairs[::-1])
