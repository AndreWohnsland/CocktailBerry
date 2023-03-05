from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.logwindow import Ui_LogWindow


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
        self.move(0, 0)
        UI_LANGUAGE.adjust_log_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
