import sys
from PyQt5.QtWidgets import QApplication

from src.error_handler import logerror
from src.ui.setup_mainwindow import MainScreen


@logerror
def run_cocktailberry():
    """Executes the cocktail program"""
    app = QApplication(sys.argv)
    MainScreen()
    sys.exit(app.exec_())
