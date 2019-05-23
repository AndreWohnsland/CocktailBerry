import sys
import sqlite3
import logging
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import setupui
import globals
import loggerconfig
import init_newdb

# Load all global over multiple Modules passed Values
globals.initialize()

loggername = "today"
devenvironment = True
partymode = False
neednewdb = False

if not devenvironment:
    import RPi.GPIO as GPIO


if __name__ == '__main__':

    # Connect (or create) the DB and the cursor
    DB = sqlite3.connect('Datenbank.db')
    c = DB.cursor()
    if neednewdb:
        init_newdb.create_new_db(DB, c)

    # Load the UI
    app = QApplication(sys.argv)
    # w = loadUi("Cocktailmanager_2.ui")
    w = setupui.MainScreen(devenvironment)

    # Setting the Pins if not DevEnvironment
    if not devenvironment:
        GPIO.setmode(GPIO.BCM)

    # Get the basic Logger
    loggerconfig.basiclogger(loggername)

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
