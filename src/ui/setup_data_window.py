from PyQt5.QtWidgets import QMainWindow

from src.filepath import SAVE_FOLDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.save_handler import SAVE_HANDLER
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

        self.data_files = self._get_saved_data_files()
        self.selection_data.activated.connect(self._display_data)

        self.since_reset_str = "since reset"
        self.all_time_str = "all time"
        drop_down_options = [self.since_reset_str, self.all_time_str] + self.data_files
        DP_CONTROLLER.fill_single_combobox(self.selection_data, drop_down_options, first_empty=False)
        UI_LANGUAGE.adjust_data_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _get_saved_data_files(self):
        """Checks the logs folder for all existing log files"""
        return [file.name for file in SAVE_FOLDER.glob("*Recipe*.csv")]

    def _display_data(self):
        selection = self.selection_data.currentText()
        print(f"TODO: {selection}")
        if selection == self.all_time_str:
            print("Getting all data from db")
        elif selection == self.since_reset_str:
            print("Getting data since reset")
        else:
            print("getting data from file")
