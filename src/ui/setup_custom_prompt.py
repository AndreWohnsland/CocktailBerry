from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.customprompt import Ui_CustomPrompt


class CustomPrompt(QMainWindow, Ui_CustomPrompt):
    """Creates the Password Widget."""

    user_okay = pyqtSignal(bool)

    def __init__(self, information: str) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.yes_button.clicked.connect(self._yes_clicked)
        self.no_button.clicked.connect(self._no_clicked)
        self.information.setText(information)
        UI_LANGUAGE.adjust_custom_prompt(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _yes_clicked(self) -> None:
        """Accept the message."""
        self.user_okay.emit(True)

    def _no_clicked(self) -> None:
        """Rejects the message."""
        self.user_okay.emit(False)
