from PyQt5.QtCore import pyqtSignal, QPoint
from PyQt5.QtWidgets import QLabel

# threshold that scroll over a label is not considered a click
# if the distance is too large
MAX_SCROLL_DISTANCE = 20


class ClickableLabel(QLabel):
    """ Additional class to add a click event to the QLineEdit. """
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.isPressed = False
        self.pressPos = QPoint()

    def mousePressEvent(self, event):
        self.isPressed = True
        self.pressPos = event.pos()
        QLabel.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.isPressed and self.rect().contains(event.pos()):
            releasePos = event.pos()
            if (releasePos - self.pressPos).manhattanLength() < MAX_SCROLL_DISTANCE:
                self.clicked.emit()
        self.isPressed = False
        QLabel.mouseReleaseEvent(self, event)
