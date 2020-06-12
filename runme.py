import sys
import sqlite3
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import src_ui.setupui as setupui
import globals
from src.logger_handler import LoggerHandler

globals.initialize()
devenvironment = True
PARTYMODE = False

if not devenvironment:
    import RPi.GPIO as GPIO


if __name__ == "__main__":

    # Connect (or create) the DB and the cursor
    dbname = "Cocktail_database"
    dirpath = os.path.dirname(__file__)
    db_path = os.path.join(dirpath, "{}.db".format(dbname))
    DB = sqlite3.connect(db_path)
    c = DB.cursor()

    # Setting the Pins if not DevEnvironment
    if not devenvironment:
        GPIO.setmode(GPIO.BCM)

    # Get the basic Logger
    logger_handler = LoggerHandler("cocktail_application", "production_logs", new_handler=True)
    logger_handler.log_start_program()

    app = QApplication(sys.argv)
    w = setupui.MainScreen(devenvironment, db_path)
    setupui.pass_setup(w, DB, c, PARTYMODE, devenvironment)
    w.showFullScreen()
    w.setFixedSize(800, 480)

    sys.exit(app.exec_())
    DB.close()
    # Code for hide the curser. Still experimental!
    # w.setCursor(Qt.BlankCursor)
    # for count in range(1,10):
    # 	CBSname = getattr(w, "CBB" + str(count))
    # 	CBSname.setCursor(Qt.BlankCursor)
