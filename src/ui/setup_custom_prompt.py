from PyQt6.QtCore import QEventLoop
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.customprompt import Ui_CustomPrompt


class CustomPrompt(QMainWindow, Ui_CustomPrompt):
    """Creates the Password Widget."""

    def __init__(self, information: str) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.yes_button.clicked.connect(self._yes_clicked)
        self.no_button.clicked.connect(self._no_clicked)
        self._result = False
        self.information.setText(information)
        UI_LANGUAGE.adjust_custom_prompt(self)

    def _yes_clicked(self) -> None:
        self._finish(True)

    def _no_clicked(self) -> None:
        self._finish(False)

    def _finish(self, result: bool) -> None:
        """Store result and quit loop if running."""
        self._result = result
        if self._loop is not None:
            self._loop.quit()
        self.close()

    def exec(self) -> bool:
        """Show the prompt and block until user chooses."""
        self._loop = QEventLoop()
        self.destroyed.connect(self._loop.quit)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        self._loop.exec()
        return self._result

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if self._loop is not None and self._loop.isRunning():
            self._finish(False)
        super().closeEvent(event)
