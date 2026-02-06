from typing import TYPE_CHECKING

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.tabs.maker import interrupt_cocktail
from src.ui_elements.progressbarwindow import Ui_Progressbarwindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class ProgressScreen(QMainWindow, Ui_Progressbarwindow):
    """Class for the Progress screen during Cocktail making."""

    def __init__(self, parent: "MainScreen", cocktail_type: str = "Cocktail") -> None:
        """Initialize the Progress screen."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.PBabbrechen.clicked.connect(interrupt_cocktail)
        self.mainscreen = parent
        self.show_screen(cocktail_type)

    def show_screen(self, cocktail_type: str = "Cocktail") -> None:
        """Show the Progress screen."""
        UI_LANGUAGE.adjust_progress_screen(self, cocktail_type)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        interrupt_cocktail()
        super().closeEvent(a0)
