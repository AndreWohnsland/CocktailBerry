from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
from collections import Counter

from ui_elements.handadds import Ui_handadds
from src.display_handler import DisplayHandler
from src.database_commander import DatabaseCommander

display_handler = DisplayHandler()
database_commander = DatabaseCommander()


class HandaddWidget(QDialog, Ui_handadds):
    """ Creates a window where the user can define additional ingredients to add via hand after the machine. """

    def __init__(self, parent):
        super(HandaddWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.ms = parent
        self.setWindowIcon(QIcon(parent.icon_path))
        hand_list = database_commander.get_ingredient_names_hand()
        machine_list = database_commander.get_ingredient_names_machine()
        hand_list.sort()
        machine_list.sort()
        ingredient_list = hand_list + machine_list
        self.comboboxes_handadd = [getattr(self, f"CBHandadd{x}") for x in range(1, 6)]
        display_handler.fill_multiple_combobox(self.comboboxes_handadd, ingredient_list, sort_items=False)
        # connect the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)

        self.lineedit_hand = [getattr(self, f"LEHandadd{x}") for x in range(1, 6)]
        for lineedit in self.lineedit_hand:
            lineedit.clicked.connect(
                lambda o=lineedit: self.ms.passwordwindow(le_to_write=o, x_pos=400, y_pos=50, headertext="Menge eingeben!")
            )
            lineedit.setValidator(QIntValidator(0, 300))
            lineedit.setMaxLength(3)
        self.fill_elements()
        self.move(0, 100)

    def fill_elements(self):
        for i, row in enumerate(self.ms.handaddlist, start=1):
            ingredient_name = database_commander.get_ingredient_name_from_id(row[0])
            combobox = getattr(self, f"CBHandadd{i}")
            lineedit = getattr(self, f"LEHandadd{i}")
            display_handler.set_combobox_item(combobox, ingredient_name)
            lineedit.setText(str(row[1]))

    def abbrechen_clicked(self):
        """ Closes the window without any action. """
        self.close()

    def eintragen_clicked(self):
        """ Closes the window and enters the values into the DB/LE. """
        ingredient_list = []
        amount_list = []
        # checks for each row if both values are nothing or a value (you need both for a valid entry)
        for i in range(1, 6):
            lineedit = getattr(self, f"LEHandadd{i}")
            combobox = getattr(self, f"CBHandadd{i}")
            if self.missing_pairs(combobox, lineedit):
                display_handler.standard_box("Irgendwo ist ein Wert vergessen worden!")
                return
            # append both values to the lists
            elif combobox.currentText() != "":
                ingredient_list.append(combobox.currentText())
                amount_list.append(int(lineedit.text()))
        # check if any ingredient was used twice
        counted_ingredients = Counter(ingredient_list)
        double_ingredient = [x[0] for x in counted_ingredients.items() if x[1] > 1]
        if len(double_ingredient) != 0:
            display_handler.standard_box(f"Eine der Zutaten:\n<{double_ingredient[0]}>\nwurde doppelt verwendet!")
            return
        # if it passes all tests, generate the list for the later entry ands enter the comment into the according field
        self.ms.handaddlist = []
        commenttext = ""
        for ingredient, amount in zip(ingredient_list, amount_list):
            ingredient_data = database_commander.get_ingredient_data(ingredient)
            alcoholic = 1 if ingredient_data["alcohollevel"] > 0 else 0
            self.ms.handaddlist.append([ingredient_data["ID"], amount, alcoholic, 1, ingredient_data["alcohollevel"]])
            commenttext += f"{amount} ml {ingredient}, "
        commenttext = commenttext[:-2]
        self.ms.LEKommentar.setText(commenttext)
        self.close()

    def missing_pairs(self, combobox, lineedit):
        if ((combobox.currentText() != "") and lineedit.text() == "") or ((combobox.currentText() == "") and lineedit.text() != ""):
            return True
        return False
