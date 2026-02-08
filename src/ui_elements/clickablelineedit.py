from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLineEdit


class ClickableLineEdit(QLineEdit):
    """ Additional class to add a click event to the QLineEdit. """
    clicked = pyqtSignal()

    def mousePressEvent(self, event):  # ty:ignore[invalid-method-override]
        self.clicked.emit()
        QLineEdit.mousePressEvent(self, event)
