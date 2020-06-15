import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import src_ui.setup_mainwindow as setupui
import globals
from src.logger_handler import LoggerHandler

globals.initialize()


if __name__ == "__main__":

    # Connect (or create) the DB and the cursor
    dbname = "Cocktail_database"
    dirpath = os.path.dirname(__file__)
    db_path = os.path.join(dirpath, f"{dbname}.db")

    # Get the basic Logger
    logger_handler = LoggerHandler("cocktail_application", "production_logs")
    logger_handler.log_start_program()

    app = QApplication(sys.argv)
    w = setupui.MainScreen(db_path)
    w.showFullScreen()
    w.setFixedSize(800, 480)

    sys.exit(app.exec_())
