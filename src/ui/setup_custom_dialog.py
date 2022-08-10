from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from src.ui_elements.customdialog import Ui_CustomDialog
from src.display_controller import DP_CONTROLLER


class CustomDialog(QDialog, Ui_CustomDialog):
    """ Class for the Team selection Screen. """

    def __init__(self, message: str, title: str = "Information", icon_path: Optional[str] = None):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.inject_stylesheet(self)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.informationLabel.setText(message)
        self.setWindowTitle(title)
        self.closeButton.clicked.connect(self.close_clicked)
        self.setWindowIcon(QIcon(icon_path))
        self.move(0, 0)
        DP_CONTROLLER.set_display_settings(self)

    def close_clicked(self):
        self.close()
