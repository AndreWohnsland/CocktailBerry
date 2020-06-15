from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from ui_elements.progressbarwindow import Ui_Progressbarwindow

from src.maker import abbrechen_R


class ProgressScreen(QMainWindow, Ui_Progressbarwindow):
    """ Class for the Progressscreen during Cocktail making. """

    def __init__(self, parent=None):
        super(ProgressScreen, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.PBabbrechen.clicked.connect(lambda: abbrechen_R())
        self.setWindowIcon(QIcon("Cocktail-icon.png"))
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
