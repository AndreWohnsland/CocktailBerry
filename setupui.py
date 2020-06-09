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
from helperfunctions import export_ingredients, export_recipes, plusminus
from bottles import Belegung_progressbar
from msgboxgenerate import standartbox

from ui_elements.Cocktailmanager_2 import Ui_MainWindow
from ui_elements.passwordbuttons import Ui_PasswordWindow
from ui_elements.passwordbuttons2 import Ui_PasswordWindow2
from ui_elements.progressbarwindow import Ui_Progressbarwindow
from ui_elements.bonusingredient import Ui_addingredient
from ui_elements.bottlewindow import Ui_Bottlewindow
from ui_elements.Keyboard import Ui_Keyboard
from ui_elements.handadds import Ui_handadds
from ui_elements.available import Ui_available


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
        self.handaddlist = []
        # the connection method here is defined in a seperate file "clickablelineedit.py"
        # even if it belongs to the UI if its moved there, there will be an import error.
        # Till this problem is resolved, this file will stay in the main directory
        self.LEpw.clicked.connect(lambda: self.passwordwindow(self.LEpw))
        self.LEpw2.clicked.connect(lambda: self.passwordwindow(self.LEpw2))
        self.LECleanMachine.clicked.connect(lambda: self.passwordwindow(self.LECleanMachine))
        self.LECocktail.clicked.connect(lambda: self.keyboard(self.LECocktail))
        self.LEGehaltRezept.clicked.connect(
            lambda: self.passwordwindow(self.LEGehaltRezept, y_pos=50, headertext="Alkoholgehalt eingeben!")
        )
        self.LEZutatRezept.clicked.connect(lambda: self.keyboard(self.LEZutatRezept, max_char_len=20))
        self.LEKommentar.clicked.connect(self.handwindow)
        self.PBAvailable.clicked.connect(self.availablewindow)
        # connects all the Lineedits from the Recipe amount and gives them the validator
        LER_obj = [getattr(self, "LER" + str(x)) for x in range(1, 9)]
        for obj in LER_obj:
            obj.clicked.connect(lambda o=obj: self.passwordwindow(le_to_write=o, x_pos=400, y_pos=50, headertext="Zutatenmenge eingeben!",))
            obj.setValidator(QIntValidator(0, 300))
            obj.setMaxLength(3)
        # Setting up Validators for all the the fields (length and/or Types):
        self.LEGehaltRezept.setValidator(QIntValidator(0, 99))
        self.LEGehaltRezept.setMaxLength(2)
        self.LEZutatRezept.setMaxLength(20)
        self.LEFlaschenvolumen.setValidator(QIntValidator(100, 2000))
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
        self.kbw = KeyboardWidget(self, le_to_write=le_to_write, max_char_len=max_char_len)
        if headertext is not None:
            self.kbw.setWindowTitle(headertext)
        self.kbw.showFullScreen()

    def progressionqwindow(self, labelchange=False):
        """ Opens up the progressionwindow to show the Cocktail status. """
        self.prow = ProgressScreen(self)
        if labelchange:
            self.prow.Lheader.setText("Zutat wird ausgegeben!\nFortschritt:")
        self.prow.show()

    def prow_change(self, pbvalue):
        """ Changes the value of the Progressionbar of the ProBarWindow. """
        self.prow.progressBar.setValue(pbvalue)

    def prow_close(self):
        """ Closes the Progressionwindow at the end of the cyclus. """
        self.prow.close()

    def bottleswindow(self, bot_names=[], vol_values=[]):
        """ Opens the bottlewindow to change the volumelevels. """
        self.botw = BottleWindow(self)
        self.botw.show()

    def ingredientdialog(self):
        """ Opens a window to spend one single ingredient. """
        self.ingd = GetIngredientWindow(self)
        self.ingd.show()

    def handwindow(self):
        """ Opens a window to enter additional ingrediends added by hand. """
        if self.LWRezepte.selectedItems() and self.handaddlist == []:
            storeval = self.c.execute(
                "SELECT Z.Zutaten_ID, Z.Menge, Z.Alkoholisch FROM Zusammen AS Z INNER JOIN Rezepte AS R ON R.ID=Z.Rezept_ID WHERE R.Name = ? AND Z.Hand=1",
                (self.LWRezepte.currentItem().text(),),
            )
            for row in storeval:
                self.handaddlist.append(list(row))
        self.handw = HandaddWidget(self)
        self.handw.show()

    def availablewindow(self):
        self.availw = AvailableWindow(self)
        self.availw.showFullScreen()


class ProgressScreen(QMainWindow, Ui_Progressbarwindow):
    """ Class for the Progressscreen during Cocktail making. """

    def __init__(self, parent=None):
        super(ProgressScreen, self).__init__(parent)
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
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
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


class BottleWindow(QMainWindow, Ui_Bottlewindow):
    """ Creates the Window to change to levels of the bottles. """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons, gets the names from Mainwindow/DB. """
        super(BottleWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # connects all the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)
        # sets cursor visualibility and assigns the names to the labels
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        for i in range(1, 11):
            CBBname = getattr(self.ms, "CBB" + str(i))
            labelobj = getattr(self, "LName" + str(i))
            labelobj.setText("    " + CBBname.currentText())
        self.DB = self.ms.DB
        self.c = self.ms.c
        # get all the DB values and assign the nececary to the level labels
        # note: since there can be blank bottles (id=0 so no match) this needs to be catched as well (no selection from DB)
        self.IDlist = []
        self.maxvolume = []
        for flasche in range(1, 11):
            bufferlevel = self.c.execute(
                "SELECT Zutaten.Mengenlevel, Zutaten.ID, Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID AND Belegung.Flasche = ?",
                (flasche,),
            ).fetchone()
            LName = getattr(self, "LAmount" + str(flasche))
            if bufferlevel is not None:
                LName.setText(str(bufferlevel[0]))
                self.IDlist.append(bufferlevel[1])
                self.maxvolume.append(bufferlevel[2])
            else:
                LName.setText("0")
                self.IDlist.append(0)
                self.maxvolume.append(0)
        # creates lists of the objects and assings functions later through a loop
        myplus = [getattr(self, "PBMplus" + str(x)) for x in range(1, 11)]
        myminus = [getattr(self, "PBMminus" + str(x)) for x in range(1, 11)]
        mylabel = [getattr(self, "LAmount" + str(x)) for x in range(1, 11)]
        for plus, minus, field, vol in zip(myplus, myminus, mylabel, self.maxvolume):
            plus.clicked.connect(lambda _, l=field, b=vol: plusminus(label=l, operator="+", minimal=50, maximal=b, dm=25))
            minus.clicked.connect(lambda _, l=field, b=vol: plusminus(label=l, operator="-", minimal=50, maximal=b, dm=25))

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def eintragen_clicked(self):
        """ Enters the Data and closes the window. """
        for i in range(1, 11):
            LName = getattr(self, "LAmount" + str(i))
            new_amount = min(int(LName.text()), self.maxvolume[i - 1])
            self.c.execute(
                "UPDATE OR IGNORE Zutaten SET Mengenlevel = ? WHERE ID = ?", (new_amount, self.IDlist[i - 1]),
            )
        self.DB.commit()
        Belegung_progressbar(self.ms, self.DB, self.c)
        self.close()


class GetIngredientWindow(QDialog, Ui_addingredient):
    """ Creates a Dialog to chose an additional ingredient and the amount
    to spend this ingredient.
    """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons and get values for the Combobox. """
        super(GetIngredientWindow, self).__init__(parent)
        self.setupUi(self)
        # Set window properties
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon("Cocktail-icon.png"))
        self.ms = parent
        if not self.ms.devenvironment:
            self.setCursor(Qt.BlankCursor)
        # Connect all the buttons
        self.PBplus.clicked.connect(lambda: plusminus(self.LAmount, "+", 20, 100, 10))
        self.PBminus.clicked.connect(lambda: plusminus(self.LAmount, "-", 20, 100, 10))
        self.PBAusgeben.clicked.connect(self.ausgeben_clicked)
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        # Get the DB and fill Combobox
        self.DB = self.ms.DB
        self.c = self.ms.c
        bottles = self.c.execute("SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID")
        for bottle in bottles:
            self.CBingredient.addItem(bottle[0])

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
        pins = globals.USEDPINS
        volumeflows = globals.PUMP_VOLUMEFLOW
        globals.loopcheck = True
        # select the bottle and the according pin as well as Volumeflow, calculates the needed time
        bottlename = self.CBingredient.currentText()
        bottle = self.c.execute("SELECT Flasche From Belegung WHERE Zutat_F = ?", (bottlename,)).fetchone()
        if bottle is not None:
            pos = bottle[0] - 1
            print(f"Ausgabemenge von {self.CBingredient.currentText()}: {self.LAmount.text()} die Flaschennummer ist: {pos + 1}")
        pin = pins[pos]
        volumeflow = int(volumeflows[pos])
        volume = int(self.LAmount.text())
        check = True
        # now checks if there is enough of the ingredient
        amounttest = self.c.execute("SELECT Mengenlevel FROM Zutaten WHERE Name = ? and Mengenlevel < ?", (bottlename, volume),).fetchone()
        if amounttest is not None:
            missingamount = amounttest[0]
            standartbox(f"Die Flasche hat nicht genug Volumen! {volume} ml werden gebraucht, {missingamount} ml sind vorhanden!")
            check = False
        if check:
            time_needed = volume / volumeflow
            time_actual = 0
            # initialise and open the Pins = activate the pump
            if not self.ms.devenvironment:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, 0)
            print(f"Pin: {pin} wurde initialisiert!")
            self.close()
            self.ms.progressionqwindow(labelchange=True)
            # until the time is reached, or the process is interrupted loop:
            while time_actual < time_needed and globals.loopcheck:
                if (time_actual) % 1 == 0:
                    print(str(time_actual) + " von " + str(time_needed) + " Sekunden ")
                time_actual += timestep
                time_actual = round(time_actual, 2)
                time.sleep(timestep)
                self.ms.prow_change(time_actual / time_needed * 100)
                qApp.processEvents()
            # close the pin / pump at the end of the process.
            if not self.ms.devenvironment:
                GPIO.output(pin, 1)
            # checks if the program was interrupted before or carried out till the end, gets the used volume
            if not globals.loopcheck:
                volume_to_substract = int(round(time_actual * volumeflow, 0))
            else:
                volume_to_substract = volume
            # substract the volume from the DB
            self.c.execute(
                "UPDATE OR IGNORE Zutaten SET Mengenlevel = Mengenlevel - ?, Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ?  WHERE Name = ?",
                (volume_to_substract, volume_to_substract, volume_to_substract, bottlename,),
            )
            self.DB.commit()
            self.ms.prow_close()


class KeyboardWidget(QDialog, Ui_Keyboard):
    """ Creates a Keyboard where the user can enter names or similar strings to Lineedits. """

    def __init__(self, parent, le_to_write=None, max_char_len=30):
        super(KeyboardWidget, self).__init__(parent)
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


class HandaddWidget(QDialog, Ui_handadds):
    """ Creates a window where the user can define additional ingredients to add via hand after the machine. """

    def __init__(self, parent):
        super(HandaddWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.ms = parent
        self.setWindowIcon(QIcon("Cocktail-icon.png"))
        # get all ingredients from the DB (all of them, handadd and normal, bc you may want to add normal as well)
        # first get a sortet list of all hand ingredients
        handingredients = self.ms.c.execute("SELECT Name FROM Zutaten WHERE Hand = 1")
        hand_list = [ingredient[0] for ingredient in handingredients]
        hand_list.sort()
        # then get a sorted list of all normal ingredients
        normalingredients = self.ms.c.execute("SELECT Name FROM Zutaten WHERE Hand = 0")
        normal_list = [ingredient[0] for ingredient in normalingredients]
        normal_list.sort()
        # combines both list, the normal at the bottom, since you want use them as often as the hand ones
        ing_list = hand_list + normal_list
        # goes through all CB and assign a empty value and all other listvalies
        for i in range(1, 6):
            CBhand = getattr(self, "CBHandadd" + str(i))
            CBhand.addItem("")
            for ing in ing_list:
                CBhand.addItem(ing)
        # connect the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)
        for i in range(1, 6):
            LEHand = getattr(self, "LEHandadd" + str(i))
            LEHand.clicked.connect(
                lambda o=LEHand: self.ms.passwordwindow(le_to_write=o, x_pos=400, y_pos=50, headertext="Menge eingeben!")
            )
            LEHand.setValidator(QIntValidator(0, 300))
            LEHand.setMaxLength(3)
        for i, row in enumerate(self.ms.handaddlist):
            ing_name = self.ms.c.execute("SELECT Name FROM Zutaten WHERE ID = ?", (row[0],)).fetchone()[0]
            cb_obj = getattr(self, "CBHandadd" + str(i + 1))
            le_obj = getattr(self, "LEHandadd" + str(i + 1))
            index = cb_obj.findText(ing_name, Qt.MatchFixedString)
            cb_obj.setCurrentIndex(index)
            le_obj.setText(str(row[1]))
        self.move(0, 100)

    def abbrechen_clicked(self):
        """ Closes the window without any action. """
        self.close()

    def eintragen_clicked(self):
        """ Closes the window and enters the values into the DB/LE. """
        inglist = []
        amountlist = []
        # checks for each row if both values are nothing or a value (you need both for a valid entry)
        for i in range(1, 6):
            LEname = getattr(self, "LEHandadd" + str(i))
            CBname = getattr(self, "CBHandadd" + str(i))
            if ((CBname.currentText() != "") and LEname.text() == "") or ((CBname.currentText() == "") and LEname.text() != ""):
                standartbox("Irgendwo ist ein Wert vergessen worden!")
                return
            # append both values to the lists
            elif (CBname.currentText() != "") and LEname.text() != "":
                inglist.append(CBname.currentText())
                amountlist.append(int(LEname.text()))
        # check if any ingredient was used twice
        counted_ing = Counter(inglist)
        double_ing = [x[0] for x in counted_ing.items() if x[1] > 1]
        if len(double_ing) != 0:
            standartbox(f"Eine der Zutaten:\n<{double_ing[0]}>\nwurde doppelt verwendet!")
            return
        # if it passes all tests, generate the list for the later entry ands enter the comment into the according field
        self.ms.handaddlist = []
        commenttext = ""
        for ing, amount in zip(inglist, amountlist):
            db_buffer = self.ms.c.execute("SELECT ID, ALkoholgehalt FROM Zutaten WHERE Name = ?", (ing,)).fetchone()
            alcoholic = 0
            if db_buffer[1] > 0:
                alcoholic = 1
            self.ms.handaddlist.append([db_buffer[0], amount, alcoholic, 1, db_buffer[1]])
            commenttext += "{} ml {}, ".format(amount, ing)
        if len(commenttext) > 0:
            commenttext = commenttext[:-2]
        self.ms.LEKommentar.setText(commenttext)
        self.close()


class AvailableWindow(QMainWindow, Ui_available):
    """ Opens a window where the user can select all available ingredients. """

    def __init__(self, parent):
        super(AvailableWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ms = parent
        # somehow the ui dont accept without _2 for those two buttons so they are _2
        self.PBAbbruch_2.clicked.connect(self.abbrechen_clicked)
        self.PBOk_2.clicked.connect(self.accepted_clicked)
        self.PBAdd.clicked.connect(lambda: self.changeingredient(self.LWVorhanden, self.LWAlle))
        self.PBRemove.clicked.connect(lambda: self.changeingredient(self.LWAlle, self.LWVorhanden))
        # gets the available ingredients out of the DB and assigns them to the LW
        cursor_buffer = self.ms.c.execute("SELECT Z.Name FROM Zutaten AS Z INNER JOIN Vorhanden AS V ON V.ID = Z.ID")
        ingredient_available = []
        for name in cursor_buffer:
            self.LWVorhanden.addItem(name[0])
            ingredient_available.append(name[0])
        # gets the names of all ingredients out of the DB calculates the not used ones and assigns them to the LW
        cursor_buffer = self.ms.c.execute("SELECT Name FROM Zutaten")
        ingredient_all = []
        for name in cursor_buffer:
            ingredient_all.append(name[0])
        entrylist = list(set(ingredient_all) - set(ingredient_available))
        for name in entrylist:
            self.LWAlle.addItem(name)
        # generates two list for values to remove and add from the db when the accept button is clicked
        # self.add_db = []
        # self.remove_db = []

    def abbrechen_clicked(self):
        """ Closes the window without any furter action. """
        self.close()

    def accepted_clicked(self):
        """ Writes the new availibility into the DB. """
        self.ms.c.execute("DELETE FROM Vorhanden")
        for i in range(self.LWVorhanden.count()):
            ing_id = self.ms.c.execute("SELECT ID FROM Zutaten WHERE Name=?", (self.LWVorhanden.item(i).text(),),).fetchone()[0]
            self.ms.c.execute("INSERT OR IGNORE INTO Vorhanden(ID) VALUES(?)", (ing_id,))
        self.ms.DB.commit()
        # reloads the maker screen and updates the shown available recipes
        Rezepte_a_M(self.ms, self.ms.DB, self.ms.c)
        Maker_List_null(self.ms, self.ms.DB, self.ms.c)
        self.close()

    def changeingredient(self, lwadd, lwremove):
        if not lwremove.selectedItems():
            return

        ingredientname = lwremove.currentItem().text()
        lwadd.addItem(ingredientname)
        delfind = lwremove.findItems(ingredientname, Qt.MatchExactly)
        if len(delfind) > 0:
            for item in delfind:
                lwremove.takeItem(lwremove.row(item))
        for i in range(lwremove.count()):
            lwremove.item(i).setSelected(False)


def pass_setup(w, DB, c, partymode, devenvironment):
    """ Connect all the functions with the Buttons. """
    # First, connect all the Pushbuttons with the Functions
    w.PBZutathinzu.clicked.connect(lambda: enter_ingredient(w, DB, c))
    w.PBRezepthinzu.clicked.connect(lambda: Rezept_eintragen(w, DB, c, True))
    w.PBBelegung.clicked.connect(lambda: customlevels(w, DB, c))
    w.PBZeinzelnd.clicked.connect(lambda: custom_output(w, DB, c))
    w.PBclear.clicked.connect(lambda: Rezepte_clear(w, DB, c, True))
    w.PBRezeptaktualisieren.clicked.connect(lambda: Rezept_eintragen(w, DB, c, False))
    w.PBdelete.clicked.connect(lambda: Rezepte_delete(w, DB, c))
    w.PBZdelete.clicked.connect(lambda: Zutaten_delete(w, DB, c))
    w.PBZclear.clicked.connect(lambda: Zutaten_clear(w, DB, c))
    w.PBZaktualisieren.clicked.connect(lambda: enter_ingredient(w, DB, c, False))
    w.PBZubereiten_custom.clicked.connect(lambda: Maker_Zubereiten(w, DB, c, devenvironment))
    w.PBCleanMachine.clicked.connect(lambda: CleanMachine(w, DB, c, devenvironment))
    w.PBFlanwenden.clicked.connect(lambda: Belegung_Flanwenden(w, DB, c))
    w.PBZplus.clicked.connect(lambda: plusminus(w.LEFlaschenvolumen, "+", 500, 1500, 50))
    w.PBZminus.clicked.connect(lambda: plusminus(w.LEFlaschenvolumen, "-", 500, 1500, 50))
    w.PBMplus.clicked.connect(lambda: plusminus(w.LCustomMenge, "+", 100, 400, 25))
    w.PBMminus.clicked.connect(lambda: plusminus(w.LCustomMenge, "-", 100, 400, 25))
    w.PBSetnull.clicked.connect(lambda: Maker_nullProB(w, DB, c))
    w.PBZnull.clicked.connect(lambda: export_ingredients(w))
    w.PBRnull.clicked.connect(lambda: export_recipes(w))
    w.PBenable.clicked.connect(lambda: enableall(w, DB, c))

    # Connect the Lists with the Functions
    w.LWZutaten.itemClicked.connect(lambda: Zutaten_Zutaten_click(w, DB, c))
    w.LWZutaten.currentTextChanged.connect(lambda: Zutaten_Zutaten_click(w, DB, c))
    w.LWMaker.itemClicked.connect(lambda: Maker_Rezepte_click(w, DB, c))
    w.LWMaker.currentTextChanged.connect(lambda: Maker_Rezepte_click(w, DB, c))
    w.LWRezepte.itemClicked.connect(lambda: Rezepte_Rezepte_click(w, DB, c))
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
    newCB_Bottles(w, DB, c)
    # Load current Bottles into the Combobuttons
    Belegung_einlesen(w, DB, c)
    # Load Existing Recipes from DB into Recipe List
    Rezepte_a_R(w, DB, c)
    # Load Possible Recipes Into Maker List
    Rezepte_a_M(w, DB, c)
    # Load the Progressbar
    Belegung_progressbar(w, DB, c)

    for combobox in [getattr(w, "CBB" + str(x)) for x in range(1, 11)]:
        combobox.activated.connect(lambda _, window=w, db=DB, cursor=c: refresh_bottle_cb(w=window, DB=db, c=cursor))
