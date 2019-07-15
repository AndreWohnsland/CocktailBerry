""" Connects all the functions to the Buttons as well the Lists 
of the passed window. Also defines the Mode for controls. 
"""
import sys
import sqlite3
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import string

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
from ui_elements.Keyboard import Ui_Keyboard


class MainScreen(QMainWindow, Ui_MainWindow):
    """ Creates the Mainscreen. """

    def __init__(self, devenvironment, DB=None, parent=None):
        """ Init. Many of the button and List connects are in pass_setup. """
        super(MainScreen, self).__init__(parent)
        self.setupUi(self)
        # as long as its not devenvironment (usually touchscreen) hide the cursor
        if not devenvironment:
            self.setCursor(Qt.BlankCursor)
        self.devenvironment = devenvironment
        # connect to the DB, if one is given (you should always give one!)
        if DB is not None:
            self.DB = sqlite3.connect(DB)
            self.c = self.DB.cursor()
        # the connection method here is defined in a seperate file "clickablelineedit.py"
        # even if it belongs to the UI if its moved there, there will be an import error.
        # Till this problem is resolved, this file will stay in the main directory
        self.LEpw.clicked.connect(lambda: self.passwordwindow(self.LEpw))
        self.LEpw2.clicked.connect(lambda: self.passwordwindow(self.LEpw2))
        self.LECleanMachine.clicked.connect(lambda: self.passwordwindow(self.LECleanMachine))
        self.LECocktail.clicked.connect(lambda: self.keyboard(self.LECocktail))
        self.LEGehaltRezept.clicked.connect(lambda: self.passwordwindow(self.LEGehaltRezept, y_pos=50, headertext="Alkoholgehalt eingeben!"))
        self.LEZutatRezept.clicked.connect(lambda: self.keyboard(self.LEZutatRezept, max_char_len=20))
        self.LEmenge_a.clicked.connect(lambda: self.passwordwindow(self.LEmenge_a, x_pos=400, y_pos=50, headertext="Zusatzmenge eingeben!"))
        self.LEprozent_a.clicked.connect(lambda: self.passwordwindow(self.LEprozent_a, x_pos=400, y_pos=50, headertext="Alkoholgehalt Zusatzmenge eingeben!"))
        self.LEKommentar.clicked.connect(lambda: self.keyboard(self.LEKommentar, max_char_len=100))
        # connects all the Lineedits from the Recipe amount and gives them the validator
        LER_obj = [getattr(self, "LER" + str(x)) for x in range(1,9)]
        for obj in LER_obj:
            obj.clicked.connect(lambda o=obj: self.passwordwindow(le_to_write=o, x_pos=400, y_pos=50, headertext="Zutatenmenge eingeben!"))
            obj.setValidator(QIntValidator(0,300))
            obj.setMaxLength(3)
        # Setting up Validators for all the the fields (length and/or Types):
        self.LEGehaltRezept.setValidator(QIntValidator(0,99))
        self.LEGehaltRezept.setMaxLength(2)
        self.LEZutatRezept.setMaxLength(20)
        self.LEFlaschenvolumen.setValidator(QIntValidator(100,2000))
        self.LEmenge_a.setValidator(QIntValidator(0,300))
        self.LEmenge_a.setMaxLength(3)
        self.LEprozent_a.setValidator(QIntValidator(0,99))
        self.LEprozent_a.setMaxLength(2)
        self.LECocktail.setMaxLength(30)

    def passwordwindow(self, le_to_write, x_pos=0, y_pos=0, headertext=None):
        """ Opens up the PasswordScreen/ a Numpad to enter Numeric Values (no commas!). 
        Needs a Lineedit where the text is put in. In addition, the header of the window can be changed. 
        This is only relevant if you dont show the window in Fullscreen!
        In addition, if its not fullscreen, the postion of the upper left edge can be set in x- and y-direction.
        """
        self.pww = PasswordScreen(self, x_pos=x_pos, y_pos=y_pos, le_to_write=le_to_write)
        if headertext is not None:
            self.pww.setWindowTitle(headertext)
        self.pww.show()
    
    def keyboard(self, le_to_write, headertext=None, max_char_len=30):
        """ Opens up the Keyboard to seperate Enter a Name or similar.
        Needs a Lineedit where the text is put in. In addition, the header of the window can be changed. 
        This is only relevant if you dont show the window in Fullscreen!
        """
        self.kbw = Keyboardwidget(self, le_to_write=le_to_write, max_char_len=max_char_len)
        if headertext is not None:
            self.kbw.setWindowTitle(headertext)
        self.kbw.showFullScreen()

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

    def __init__(self, parent, x_pos=0, y_pos=0, le_to_write=None):
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
        # Connect all the buttons, generates a list of the numbers an objectnames to do that
        self.number_list = [x for x in range(10)]
        self.attribute_numbers = [getattr(self, "PB" + str(x)) for x in self.number_list]
        for obj, number in zip(self.attribute_numbers, self.number_list):
            obj.clicked.connect(lambda _, n=number: self.number_clicked(number=n))
        self.PBenter.clicked.connect(self.enter_clicked)
        self.PBdel.clicked.connect(self.del_clicked)
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        self.pwlineedit = le_to_write
        self.move(x_pos, y_pos)

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
        # connects all the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)
        # sets cursor visualibility and assigns the names to the labels
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        for i in range(1,11):
            CBBname = getattr(self.ms, 'CBB' + str(i))
            labelobj = getattr(self, 'LName' + str(i))
            labelobj.setText('    ' + CBBname.currentText())
        self.DB = self.ms.DB
        self.c = self.ms.c
        # get all the DB values and assign the nececary to the level labels
        # note: since there can be blank bottles (id=0 so no match) this needs to be catched as well (no selection from DB)
        self.IDlist = []
        self.maxvolume = []
        for flasche in range(1, 11):
            bufferlevel = self.c.execute("SELECT Zutaten.Mengenlevel, Zutaten.ID, Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID AND Belegung.Flasche = ?", (flasche,)).fetchone()
            LName = getattr(self, 'LAmount' + str(flasche))
            if bufferlevel is not None:
                LName.setText(str(bufferlevel[0]))
                self.IDlist.append(bufferlevel[1])
                self.maxvolume.append(bufferlevel[2])
            else:
                LName.setText("0")
                self.IDlist.append(0)
                self.maxvolume.append(0)
        # creates lists of the objects and assings functions later through a loop
        myplus = [getattr(self, "PBMplus" + str(x)) for x in range(1,11)]
        myminus = [getattr(self, "PBMminus" + str(x)) for x in range(1,11)]
        mylabel = [getattr(self, "LAmount" + str(x)) for x in range(1,11)]
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
        amount = (amount//dm)*dm
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
            self.c.execute("UPDATE OR IGNORE Zutaten SET Mengenlevel = Mengenlevel - ?, Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ?  WHERE Name = ?" ,(volume_to_substract, volume_to_substract, volume_to_substract, bottlename))
            self.DB.commit()
            self.ms.prow_close()

class Keyboardwidget(QDialog, Ui_Keyboard):
    """ Creates a Keyboard where the user can enter names or similar strings to Lineedits. """
    def __init__(self, parent, le_to_write=None, max_char_len=30):
        super(Keyboardwidget, self).__init__(parent)
        self.setupUi(self)
        self.ms = parent
        self.le_to_write = le_to_write
        self.LName.setText(self.le_to_write.text())
        # populating all the buttons
        self.backButton.clicked.connect(self.backbutton_clicked)
        self.clear.clicked.connect(self.clearbutton_clicked)
        self.enterButton.clicked.connect(self.enterbutton_clicked)
        self.space.clicked.connect(lambda: self.inputbutton_clicked(" ", " "))
        self.delButton.clicked.connect(self.delete_clicked)
        self.shift.clicked.connect(self.shift_clicked)
        # generating the lists to populate all remaining buttons via iteration
        self.number_list = [x for x in range(10)]
        self.char_list_lower = [x for x in string.ascii_lowercase]
        self.char_list_upper = [x for x in string.ascii_uppercase]
        self.attribute_chars = [getattr(self, "Button" + x) for x in self.char_list_lower]
        self.attribute_numbers = [getattr(self, "Button" + str(x)) for x in self.number_list]
        for obj, char, char2 in zip(self.attribute_chars, self.char_list_lower, self.char_list_upper):
            obj.clicked.connect(lambda _, iv=char, iv_s=char2: self.inputbutton_clicked(inputvalue=iv, inputvalue_shift=iv_s))
        for obj, char, char2 in zip(self.attribute_numbers, self.number_list, self.number_list):
            obj.clicked.connect(lambda _, iv=char, iv_s=char2: self.inputbutton_clicked(inputvalue=iv, inputvalue_shift=iv_s))
        # restricting the Lineedit to a set up Char leng
        self.LName.setMaxLength(max_char_len)

    def backbutton_clicked(self):
        """ Closes the Window without any further action. """
        self.close()
    
    def clearbutton_clicked(self):
        """ Clears the input. """
        self.LName.setText("")

    def enterbutton_clicked(self):
        """ Closes and enters the String value back to the Lineedit. """
        self.le_to_write.setText(self.LName.text())
        self.close()

    def inputbutton_clicked(self, inputvalue, inputvalue_shift):
        """ Enters the inputvalue into the field, adds it to the string.
        Can either have the normal or the shift value, if there is no difference both imput arguments are the same.
        """
        stringvalue = self.LName.text()
        if self.shift.isChecked():
            addvalue = inputvalue_shift
        else:
            addvalue = inputvalue
        stringvalue += str(addvalue)
        self.LName.setText(stringvalue)

    def delete_clicked(self):
        stringvalue = self.LName.text()
        if len(stringvalue) > 0:
            self.LName.setText(stringvalue[:-1])

    def shift_clicked(self):
        if self.shift.isChecked():
            charchoose = self.char_list_upper
        else:
            charchoose = self.char_list_lower
        for obj, char in zip(self.attribute_chars, charchoose):
            obj.setText(str(char))

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
