from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel


class ClickableLabel(QLabel):
    """Additional class to add a click event to the QLabel."""

    clicked = pyqtSignal()

    def mouseReleaseEvent(self, event):  # ty:ignore[invalid-method-override]
        if self.rect().contains(event.pos()):
            self.clicked.emit()
        QLabel.mouseReleaseEvent(self, event)
