from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from ui_elements.progressbarwindow import Ui_Progressbarwindow

from src.maker import interrupt_cocktail


class ProgressScreen(QMainWindow, Ui_Progressbarwindow):
    """ Class for the Progressscreen during Cocktail making. """

    def __init__(self, parent=None):
        super(ProgressScreen, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.PBabbrechen.clicked.connect(interrupt_cocktail)
        self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        if not self.mainscreen.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
