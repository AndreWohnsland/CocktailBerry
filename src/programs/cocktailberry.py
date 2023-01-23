import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.error_handler import logerror
from src.ui.setup_mainwindow import MainScreen


@logerror
def run_cocktailberry():
    """Executes the cocktail program"""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    app = QApplication(sys.argv)
    MainScreen()
    sys.exit(app.exec_())
