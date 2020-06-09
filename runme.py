import sys
import sqlite3
import logging
import time
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import setupui
import globals
import loggerconfig

# Load all global over multiple Modules passed Values
globals.initialize()

# Here you can change the parameters:
loggername = "today"  # under this name your logging file will be saved
# important to set to False, otherwise the GPIO-commands dont work
devenvironment = True
partymode = False  # True disables the recipe tab, that no user can change it

if not devenvironment:
    import RPi.GPIO as GPIO


if __name__ == "__main__":

    # Connect (or create) the DB and the cursor
    dbname = "Datenbank"
    dirpath = os.path.dirname(__file__)
    db_path = os.path.join(dirpath, "{}.db".format(dbname))
    DB = sqlite3.connect(db_path)
    c = DB.cursor()

    # Load the UI
    app = QApplication(sys.argv)
    # w = loadUi("Cocktailmanager_2.ui")
    w = setupui.MainScreen(devenvironment, db_path)

    # Setting the Pins if not DevEnvironment
    if not devenvironment:
        GPIO.setmode(GPIO.BCM)

    # Get the basic Logger
    loggerconfig.basiclogger("cocktail_application", loggername, True)
    loggerconfig.basiclogger("debuglog", "debuglog")
    # loggerconfig.initlogger_dec('calling', 'calling')

    # Load all the Functions from the setup script
    setupui.pass_setup(w, DB, c, partymode, devenvironment)

    # Show window in Fullscreen
    w.showFullScreen()
    w.setFixedSize(800, 480)

    # Code for hide the curser. Still experimental!
    # w.setCursor(Qt.BlankCursor)
    # for count in range(1,10):
    # 	CBSname = getattr(w, "CBB" + str(count))
    # 	CBSname.setCursor(Qt.BlankCursor)

    # at the end close the application and the DB
    sys.exit(app.exec_())
    DB.close()
