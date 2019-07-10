""" Connects all the functions to the Buttons as well the Lists 
of the passed window. Also defines the Mode for controls. 
"""
import sys
import sqlite3
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

import globals
from maker import *
from ingredients import *
from recipes import *
from bottles import *
from savehelper import save_quant
from bottles import Belegung_progressbar
from msgboxgenerate import standartbox

from ui_elements.Cocktailmanager_2 import Ui_MainWindow
from ui_elements.passwordbuttons import Ui_PasswordWindow
from ui_elements.passwordbuttons2 import Ui_PasswordWindow2
from ui_elements.progressbarwindow import Ui_Progressbarwindow
from ui_elements.bonusingredient import Ui_addingredient
from ui_elements.bottlewindow import Ui_Bottlewindow


class MainScreen(QMainWindow, Ui_MainWindow):
    """ Creates the Mainscreen. """

    def __init__(self, devenvironment, DB=None, parent=None):
        """ Init. Many of the button and List connects are in pass_setup. """
        super(MainScreen, self).__init__(parent)
        self.setupUi(self)
        self.LEpw.selectionChanged.connect(lambda: self.passwordwindow(1))
        self.LEpw2.selectionChanged.connect(lambda: self.passwordwindow(2))
        self.LECleanMachine.selectionChanged.connect(lambda: self.passwordwindow(3))
        if not devenvironment:
            self.setCursor(Qt.BlankCursor)
        self.devenvironment = devenvironment
        if DB is not None:
            self.DB = sqlite3.connect(DB)
            self.c = self.DB.cursor()

    def passwordwindow(self, register):
        """ Opens up the PasswordScreen. """
        # Since there are three different passwortlabels, it exists a window for each
        if register == 1:
            self.register = 1
            if not hasattr(self, "pw1"):
                self.pw1 = PasswordScreen(self)
            self.pw1.showMaximized()
        elif register == 2:
            self.register = 2
            if not hasattr(self, "pw2"):
                self.pw2 = PasswordScreen(self)
            self.pw2.showMaximized()
        elif register == 3:
            self.register = 3
            if not hasattr(self, "pw3"):
                self.pw3 = PasswordScreen(self)
            self.pw3.showMaximized()

    def progressionqwindow(self, labelchange=False):
        """ Opens up the progressionwindow to show the Cocktail status. """
        self.prow = Progressscreen(self)
        if labelchange:
            self.prow.Lheader.setText('Zutat wird ausgegeben!\nFortschritt:')
        self.prow.show()

    def prow_change(self, pbvalue):
        """ Changes the value of the Progressionbar of the ProBarWindow. """
        self.prow.progressBar.setValue(pbvalue)

    def prow_close(self):
        """ Closes the Progressionwindow at the end of the cyclus. """
        self.prow.close()

    def bottleswindow(self, bot_names=[], vol_values=[]):
        """ Opens the bottlewindow to change the volumelevels. """
        self.botw = Bottlewindow(self)
        self.botw.show()

    def ingredientdialog(self):
        self.ingd = Getingredientwindow(self)
        self.ingd.show()


class Progressscreen(QMainWindow, Ui_Progressbarwindow):
    """ Class for the Progressscreen during Cocktail making. """

    def __init__(self, parent=None):
        super(Progressscreen, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.PBabbrechen.clicked.connect(lambda: abbrechen_R())
        self.setWindowIcon(QIcon("Cocktail-icon.png"))
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)


class PasswordScreen(QDialog, Ui_PasswordWindow2):
    """ Creates the Passwordscreen. """

    def __init__(self, parent=None):
        """ Init. Connect all the buttons and set window policy. """
        super(PasswordScreen, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(
            Qt.Window |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowStaysOnTopHint
            )
        self.setWindowIcon(QIcon("Cocktail-icon.png"))
        self.PB0.clicked.connect(lambda: self.number_clicked(0))
        self.PB1.clicked.connect(lambda: self.number_clicked(1))
        self.PB2.clicked.connect(lambda: self.number_clicked(2))
        self.PB3.clicked.connect(lambda: self.number_clicked(3))
        self.PB4.clicked.connect(lambda: self.number_clicked(4))
        self.PB5.clicked.connect(lambda: self.number_clicked(5))
        self.PB6.clicked.connect(lambda: self.number_clicked(6))
        self.PB7.clicked.connect(lambda: self.number_clicked(7))
        self.PB8.clicked.connect(lambda: self.number_clicked(8))
        self.PB9.clicked.connect(lambda: self.number_clicked(9))
        self.PBenter.clicked.connect(self.enter_clicked)
        self.PBdel.clicked.connect(self.del_clicked)
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        # decides in which window the numbers are entered
        if self.ms.register == 1:
            self.pwlineedit = self.ms.LEpw
        elif self.ms.register == 2:
            self.pwlineedit = self.ms.LEpw2
        elif self.ms.register == 3:
            self.pwlineedit = self.ms.LECleanMachine

    def number_clicked(self, number):
        """  Adds the clicked number to the lineedit. """
        self.pwlineedit.setText(self.pwlineedit.text() + "{}".format(number))

    def enter_clicked(self):
        """ Enters/Closes the Dialog. """
        self.close()

    def del_clicked(self):
        """ Deletes the last digit in the lineedit. """
        if len(self.pwlineedit.text()) > 0:
            strstor = str(self.pwlineedit.text())
            self.pwlineedit.setText(strstor[:-1])


class Bottlewindow(QMainWindow, Ui_Bottlewindow):
    """ Creates the Window to change to levels of the bottles. """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons, gets the names from Mainwindow/DB. """
        super(Bottlewindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)

        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        for i in range(1,11):
            CBBname = getattr(self.ms, 'CBB' + str(i))
            labelobj = getattr(self, 'LName' + str(i))
            labelobj.setText('    ' + CBBname.currentText())
        self.DB = self.ms.DB
        self.c = self.ms.c
        bufferleffel = self.c.execute("SELECT Zutaten.Mengenlevel, Zutaten.ID, Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID")
        self.IDlist = []
        self.maxvolume = []
        for i, level in enumerate(bufferleffel):
            LName = getattr(self, 'LAmount' + str(i+1))
            LName.setText(str(level[0]))
            self.IDlist.append(level[1])
            self.maxvolume.append(level[2])

        # creates lists of the objects and assings functions later through a loop
        myplus =  [
            self.PBMplus1, self.PBMplus2, self.PBMplus3, self.PBMplus4, self.PBMplus5,
            self.PBMplus6, self.PBMplus7, self.PBMplus8, self.PBMplus9, self.PBMplus10
        ]
        myminus =  [
            self.PBMminus1, self.PBMminus2, self.PBMminus3, self.PBMminus4, self.PBMminus5,
            self.PBMminus6, self.PBMminus7, self.PBMminus8, self.PBMminus9, self.PBMminus10
        ]
        mylabel = [
            self.LAmount1, self.LAmount2, self.LAmount3, self.LAmount4, self.LAmount5,
            self.LAmount6, self.LAmount7, self.LAmount8, self.LAmount9, self.LAmount10
        ]

        for plus, minus, field, vol in zip(myplus, myminus, mylabel, self.maxvolume):
            plus.clicked.connect(lambda _, l=field, b=vol: self.plusminus(label=l, operator='+', bsize=b))
            minus.clicked.connect(lambda _, l=field, b=vol: self.plusminus(label=l, operator='-', bsize=b))
        
    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def eintragen_clicked(self):
        """ Enters the Data and closes the window. """
        for i in range(1, 11):
            LName = getattr(self, 'LAmount' + str(i))
            new_amount = min(int(LName.text()), self.maxvolume[i-1])
            self.c.execute("UPDATE OR IGNORE Zutaten SET Mengenlevel = ? WHERE ID = ?", (new_amount, self.IDlist[i-1]))
        self.DB.commit()
        Belegung_progressbar(self.ms, self.DB, self.c)
        self.close()
    
    def plusminus(self, label, operator, bsize):
        """ Changes the value on a given amount. Operator uses '+' or '-'.
        Limits the value to a maximum and minimum Value as well as to the current Bottlesize
        Also, always makes the value of the factor 25
        """
        minimal = 50
        maximal = 1500
        dm = 25
        amount = int(label.text())
        if operator == "+":
            amount += dm
        elif operator == "-":
            amount -= dm
        else:
            raise ValueError('operator is neither plus nor minus!')
        amount = (amount//25)*25
        # limits the value to min/max value, assigns it
        amount = max(minimal, amount)
        amount = min(maximal, amount, bsize)
        label.setText(str(amount))


class Getingredientwindow(QDialog, Ui_addingredient):
    """ Creates a Dialog to chose an additional ingredient and the amount
    to spend this ingredient.
    """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons and get values for the Combobox. """
        super(Getingredientwindow, self).__init__(parent)
        self.setupUi(self)
        # Set window properties
        self.setWindowFlags(
            Qt.Window |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowStaysOnTopHint
            )
        self.setWindowIcon(QIcon("Cocktail-icon.png"))
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        # Connect all the buttons
        self.PBplus.clicked.connect(lambda: self.plusminus('+'))
        self.PBminus.clicked.connect(lambda: self.plusminus('-'))
        self.PBAusgeben.clicked.connect(self.ausgeben_clicked)
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        # Get the DB and fill Combobox
        self.DB = self.ms.DB
        self.c = self.ms.c
        bottles = self.c.execute("SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID")
        for bottle in bottles:
            self.CBingredient.addItem(bottle[0])

    def plusminus(self, operator):
        """ Changes the value on a given amount. Operator uses '+' or '-'.
        Limits the value to a maximum and minimum Value.
        """
        minimal = 20
        maximal = 100
        dm = 10
        amount = int(self.LAmount.text())
        if operator == "+":
            amount += dm
        elif operator == "-":
            amount -= dm
        else:
            raise ValueError('operator is neither plus nor minus!')
        # limits the value to min/max value, assigns it
        amount = max(minimal, amount)
        amount = min(maximal, amount)
        self.LAmount.setText(str(amount))

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def ausgeben_clicked(self):
        """ Calls the Progressbarwindow and spends the given amount of the ingredient. """
        # get the globals, set GPIO
        import globals
        if not self.ms.devenvironment:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
        timestep = 0.05
        pins = globals.usedpins
        volumeflows = globals.pumpvolume
        globals.loopcheck = True
        # select the bottle and the according pin as well as Volumeflow, calculates the needed time
        bottlename = self.CBingredient.currentText()
        bottle = self.c.execute("SELECT Flasche From Belegung WHERE Zutat_F = ?",(bottlename,)).fetchone()
        if bottle is not None:
            pos = bottle[0] - 1
            print('Ausgabemenge von ' + self.CBingredient.currentText() + ': ' + self.LAmount.text() +' die Flaschennummer ist: ' + str(pos+1))
        pin = pins[pos]
        volumeflow = int(volumeflows[pos])
        volume = int(self.LAmount.text())
        check = True
        # now checks if there is enough of the ingredient
        amounttest = self.c.execute("SELECT Mengenlevel FROM Zutaten WHERE Name = ? and Mengenlevel < ?", (bottlename, volume)).fetchone()
        if amounttest is not None:
            missingamount = amounttest[0]
            standartbox('Die Flasche hat nicht genug Volumen! %i ml werden gebraucht, %i ml sind vorhanden!' % (volume, missingamount))
            check = False
        if check:
            time_needed = volume/volumeflow
            time_actual = 0
            # initialise and open the Pins = activate the pump
            if not self.ms.devenvironment:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, 0)
            print('Pin: ' + str(pin) + ' wurde initialisiert!')
            self.close()
            self.ms.progressionqwindow(labelchange=True)
            # until the time is reached, or the process is interrupted loop:
            while (time_actual < time_needed and globals.loopcheck):
                if (time_actual) % 1 == 0:
                    print(str(time_actual) + " von " + str(time_needed) + " Sekunden ")
                time_actual += timestep
                time_actual = round(time_actual, 2)
                time.sleep(timestep)
                self.ms.prow_change(time_actual/time_needed*100)
                qApp.processEvents()
            # close the pin / pump at the end of the process.
            if not self.ms.devenvironment:
                GPIO.output(pin, 1)
            # checks if the program was interrupted before or carried out till the end, gets the used volume
            if not globals.loopcheck:
                volume_to_substract = int(round(time_actual*volumeflow,0))
            else:
                volume_to_substract = volume
            # substract the volume from the DB
            self.c.execute("UPDATE OR IGNORE Zutaten SET Mengenlevel = Mengenlevel - ? WHERE Name = ?" ,(volume_to_substract, bottlename))
            self.DB.commit()
            self.ms.prow_close()

def pass_setup(w, DB, c, partymode, devenvironment):
    """ Connect all the functions with the Buttons. """
    # First, connect all the Pushbuttons with the Functions
    w.PBZutathinzu.clicked.connect(lambda: Zutat_eintragen(w, DB, c))
    w.PBRezepthinzu.clicked.connect(lambda: Rezept_eintragen(w, DB, c, True))
    # w.PBBelegung.clicked.connect(lambda: Belegung_eintragen(w, DB, c, True))
    w.PBBelegung.clicked.connect(lambda: customlevels(w, DB, c))
    w.PBZeinzelnd.clicked.connect(lambda: custom_output(w, DB, c))
    w.PBclear.clicked.connect(lambda: Rezepte_clear(w, DB, c, True))
    w.PBRezeptaktualisieren.clicked.connect(lambda: Rezept_eintragen(w, DB, c, False))
    w.PBdelete.clicked.connect(lambda: Rezepte_delete(w, DB, c))
    w.PBZdelete.clicked.connect(lambda: Zutaten_delete(w, DB, c))
    w.PBZclear.clicked.connect(lambda: Zutaten_clear(w, DB, c))
    w.PBZaktualisieren.clicked.connect(lambda: Zutat_eintragen(w, DB, c, False))
    w.PBZubereiten_custom.clicked.connect(lambda: Maker_Zubereiten(w, DB, c, False, devenvironment))
    w.PBCleanMachine.clicked.connect(lambda: CleanMachine(w, DB, c, devenvironment))
    w.PBFlanwenden.clicked.connect(lambda: Belegung_Flanwenden(w, DB, c))
    w.PBZplus.clicked.connect(lambda: Zutaten_Flvolumen_pm(w, DB, c, "+"))
    w.PBZminus.clicked.connect(lambda: Zutaten_Flvolumen_pm(w, DB, c, "-"))
    w.PBMplus.clicked.connect(lambda: Maker_pm(w, DB, c, "+"))
    w.PBMminus.clicked.connect(lambda: Maker_pm(w, DB, c, "-"))
    w.PBSetnull.clicked.connect(lambda: Maker_nullProB(w, DB, c))
    w.PBZnull.clicked.connect(lambda: save_quant(w, DB, c, "LEpw2", 'Zutaten_export.csv', "Zutaten", "Verbrauch", "Verbrauchsmenge"))
    w.PBRnull.clicked.connect(lambda: save_quant(w, DB, c, "LEpw", 'Rezepte_export.csv', "Rezepte", "Anzahl", "Anzahl_Lifetime", True))
    w.PBenable.clicked.connect(lambda: enableall(w, DB, c))

    # Connect the Lists with the Functions
    w.LWZutaten.itemClicked.connect(lambda: Zutaten_Zutaten_click(w, DB, c))
    w.LWMaker.itemClicked.connect(lambda: Maker_Rezepte_click(w, DB, c))
    w.LWRezepte.itemClicked.connect(lambda: Rezepte_Rezepte_click(w, DB, c))
    w.LWZutaten.currentTextChanged.connect(lambda: Zutaten_Zutaten_click(w, DB, c))
    w.LWMaker.currentTextChanged.connect(lambda: Maker_Rezepte_click(w, DB, c))
    w.LWRezepte.currentTextChanged.connect(lambda: Rezepte_Rezepte_click(w, DB, c))

    # Connects the slider
    w.HSIntensity.valueChanged.connect(lambda: Maker_ProB_change(w, DB, c))

    # Disable some of the Tabs (for the Partymode, no one can access the recipes)
    if partymode:
        w.tabWidget.setTabEnabled(2, False)

    # gets the bottle ingredients into the global list
    get_bottle_ingredients(w, DB, c)
    # Clear Help Marker
    Maker_List_null(w, DB, c)
    # Load ingredients
    Zutaten_a(w, DB, c)
    # Load Bottles into the Labels
    Belegung_a(w, DB, c)
    # Load Combobuttons Recipes
    ZutatenCB_Rezepte(w, DB, c)
    # Load Combobuttons Bottles
    newCB_Bottles(w, DB,c)
    # Load current Bottles into the Combobuttons
    Belegung_einlesen(w, DB, c)
    # Load Existing Recipes from DB into Recipe List
    Rezepte_a_R(w, DB, c)
    # Load Possible Recipes Into Maker List
    Rezepte_a_M(w, DB, c)
    # Load the Progressbar
    Belegung_progressbar(w, DB, c)

    # Connects additional Functionality to the Comboboxes
    w.CBB1.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB2.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB3.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB4.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB5.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB6.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB7.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB8.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB9.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
    w.CBB10.currentIndexChanged.connect(lambda: refresh_bottle_cb(w, DB, c))
