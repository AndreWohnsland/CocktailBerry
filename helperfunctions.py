import sys
import sqlite3
import time
import datetime
import csv
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import globals
from msgboxgenerate import standartbox
from loggerconfig import logerror, logfunction


def plusminus(label, operator, minimal=0, maximal=1000, dm=10, DB=None, c=None):
    """ A helperfunction for the plus and minusbottons. Needs at least the label for the value and the operator.
    Limits the process to a minimum and maximum value. A constant stepsize dm can be set.\n
    As operater can be used: \n
    "+":    increases the value by dm\n
    "-":    decreases the value by dm
    """
    # sets the conditions that the value can not exceed the min/max value by clicking
    try:
        value_ = int(label.text())
    except ValueError:
        if operator == "+":
            value_ = maximal
        elif operator == "-":
            value_ = minimal
    # checks the operator and raises a error if its not '+' or '-'
    if operator == "+":
        value_ += dm
    elif operator == "-":
        value_ -= dm
    else:
        raise ValueError("operator is neither plus nor minus!")
    # sets the value at a multiple of dm and limits it to min/max value
    value_ = (value_ // dm) * dm
    value_ = max(minimal, value_)
    value_ = min(maximal, value_)
    label.setText(str(value_))


@logerror
def save_quant(w, DB, c, wobject_name, filename, dbstring, searchstring1, searchstring2, where_=False):
    """ Saves all the amounts of the ingredients/recipes to a csv. 
    after that sets the variable ingredient/recipes counter to zero.
    Needs the password for that procedure.
    Needs a Filename, dbstring = Listname and the lifetime (ss1) variable (ss2) amount
    where_ == True: only values greater zero are exported
    """
    wherestring1 = ""
    wherestring2 = ""
    wobject = getattr(w, wobject_name)
    if wobject.text() == globals.masterpassword:
        dirpath = os.path.dirname(__file__)
        subfoldername = "saves"
        # generating a savename prefix for the date and remove the '-' signs
        dtime = str(datetime.date.today())
        dtime = dtime.replace("-", "")
        savepath = os.path.join(dirpath, subfoldername, dtime + "_" + filename)
        with open(savepath, mode="a", newline="") as writer_file:
            csv_writer = csv.writer(writer_file, delimiter=",")
            # csv_writer.writerow(
            #     ["----- Neuer Export von %s -----" % datetime.date.today()])
            row1 = []
            row2 = []
            if where_:
                wherestring1 = " WHERE {} > 0".format(searchstring1)
                wherestring2 = " WHERE {} > 0".format(searchstring2)
            # selects the actual use and the names and writes them
            sqlstring = "SELECT Name, {0} FROM {1}{2}".format(searchstring1, dbstring, wherestring1)
            cursor_buffer = c.execute(sqlstring)
            row1.append("date")
            row2.append(datetime.date.today())
            for row in cursor_buffer:
                row1.append(row[0])
                row2.append(row[1])
            csv_writer.writerow(row1)
            csv_writer.writerow(row2)
            # csv_writer.writerow(["----- Gesamte Mengen über Lebenszeit -----"])
            row1 = []
            row2 = []
            # selects the life time use and saves them
            sqlstring = "SELECT Name, {0} FROM {1}{2}".format(searchstring2, dbstring, wherestring2)
            cursor_buffer = c.execute(sqlstring)
            row1.append("date")
            row2.append("lifetime")
            for row in cursor_buffer:
                row1.append(row[0])
                row2.append(row[1])
            csv_writer.writerow(row1)
            csv_writer.writerow(row2)
            csv_writer.writerow([" "])
        sqlstring = "UPDATE OR IGNORE {} SET {} = 0".format(dbstring, searchstring1)
        c.execute(sqlstring)
        DB.commit()
        standartbox("Alle Daten wurden exportiert und die zurücksetzbaren Mengen zurückgesetzt!")
    else:
        standartbox("Falsches Passwort!")
    wobject.setText("")
