from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.customdialog import Ui_CustomDialog


class CustomDialog(QMainWindow, Ui_CustomDialog):
    """Class for the Team selection Screen."""

    def __init__(self, message: str, title: str = "Information", use_ok=False, close_callback: Callable | None = None):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.informationLabel.setText(message)
        self.setWindowTitle(title)
        self.closeButton.clicked.connect(self.close_clicked)
        self.close_callback = close_callback

        # self.closeButton.setText(close_text)
        UI_LANGUAGE.adjust_custom_dialog(self, use_ok)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def close_clicked(self):
        if self.close_callback is not None:
            self.close_callback()
        self.close()
