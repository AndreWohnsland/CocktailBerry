from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel


class ClickableLabel(QLabel):
    """ Additional class to add a click event to the QLineEdit. """
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        QLabel.mousePressEvent(self, event)
