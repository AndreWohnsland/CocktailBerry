from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from ui_elements.progressbarwindow import Ui_Progressbarwindow

from src.maker import interrupt_cocktail
from src.dialog_handler import UI_LANGUAGE


class ProgressScreen(QMainWindow, Ui_Progressbarwindow):
    """ Class for the Progressscreen during Cocktail making. """

    def __init__(self, parent=None, cocktail_type="Cocktail"):
        super(ProgressScreen, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.PBabbrechen.clicked.connect(interrupt_cocktail)
        self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        UI_LANGUAGE.adjust_progress_screen(self, cocktail_type)
        if not self.mainscreen.UI_DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
