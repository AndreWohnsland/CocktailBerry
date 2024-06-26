from PyQt5.QtWidgets import QDialog

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.customprompt import Ui_CustomPrompt


class CustomPrompt(QDialog, Ui_CustomPrompt):
    """Creates the Password Widget."""

    def __init__(self, information):
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.yes_button.clicked.connect(self._yes_clicked)
        self.no_button.clicked.connect(self._no_clicked)
        self.information.setText(information)
        UI_LANGUAGE.adjust_custom_prompt(self)
        DP_CONTROLLER.set_display_settings(self)

    def _yes_clicked(self):
        """Accept the message."""
        self.accept()

    def _no_clicked(self):
        """Rejects the message."""
        self.reject()
