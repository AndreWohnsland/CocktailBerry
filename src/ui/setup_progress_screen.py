from PyQt5.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.tabs.maker import interrupt_cocktail
from src.ui_elements.progressbarwindow import Ui_Progressbarwindow


class ProgressScreen(QMainWindow, Ui_Progressbarwindow):
    """Class for the Progress screen during Cocktail making."""

    def __init__(self, parent, cocktail_type="Cocktail"):
        """Initialize the Progress screen."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.PBabbrechen.clicked.connect(interrupt_cocktail)
        self.mainscreen = parent
        UI_LANGUAGE.adjust_progress_screen(self, cocktail_type)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
