import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.error_handler import logerror
from src.logger_handler import LoggerHandler
from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("cocktailberry")


@logerror
def run_cocktailberry() -> None:
    """Execute the cocktail program."""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    app = QApplication([])
    MainScreen()
    qt_code = app.exec()
    _logger.info(f"CocktailBerry exited with code {qt_code}.")
    sys.exit(qt_code)
