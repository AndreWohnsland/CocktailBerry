from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog

from src.ui_elements.customdialog import Ui_CustomDialog
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE


class CustomDialog(QDialog, Ui_CustomDialog):
    """ Class for the Team selection Screen. """

    def __init__(self, message: str, title: str = "Information", icon_path: Optional[str] = None, use_ok=False):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.inject_stylesheet(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        self.informationLabel.setText(message)
        self.setWindowTitle(title)
        self.closeButton.clicked.connect(self.close_clicked)

        # self.closeButton.setText(close_text)
        self.setWindowIcon(QIcon(icon_path))
        self.move(0, 0)
        UI_LANGUAGE.adjust_custom_dialog(self, use_ok)
        DP_CONTROLLER.set_display_settings(self)

    def close_clicked(self):
        self.close()
