from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
from collections import Counter

from ui_elements.handadds import Ui_handadds
from src.display_handler import DisplayHandler

display_handler = DisplayHandler()


class HandaddWidget(QDialog, Ui_handadds):
    """ Creates a window where the user can define additional ingredients to add via hand after the machine. """

    def __init__(self, parent):
        super(HandaddWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.ms = parent
        self.setWindowIcon(QIcon(parent.icon_path))
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
                display_handler.standard_box("Irgendwo ist ein Wert vergessen worden!")
                return
            # append both values to the lists
            elif (CBname.currentText() != "") and LEname.text() != "":
                inglist.append(CBname.currentText())
                amountlist.append(int(LEname.text()))
        # check if any ingredient was used twice
        counted_ing = Counter(inglist)
        double_ing = [x[0] for x in counted_ing.items() if x[1] > 1]
        if len(double_ing) != 0:
            display_handler.standard_box(f"Eine der Zutaten:\n<{double_ing[0]}>\nwurde doppelt verwendet!")
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
