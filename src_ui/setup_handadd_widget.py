from collections import Counter

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QIcon, QIntValidator

from ui_elements.handadds import Ui_handadds
from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from config.config_manager import shared


class HandaddWidget(QDialog, Ui_handadds):
    """ Creates a window where the user can define additional ingredients to add via hand after the machine. """

    def __init__(self, parent):
        super(HandaddWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint |
                            Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.mainscreen = parent
        self.setWindowIcon(QIcon(parent.icon_path))
        hand_list = DB_COMMANDER.get_ingredient_names_hand()
        machine_list = DB_COMMANDER.get_ingredient_names_machine()
        hand_list.sort()
        machine_list.sort()
        ingredient_list = hand_list + machine_list
        self.comboboxes_handadd = [getattr(self, f"CBHandadd{x}") for x in range(1, 6)]
        DP_CONTROLLER.fill_multiple_combobox(self.comboboxes_handadd, ingredient_list, sort_items=False)
        # connect the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)

        self.lineedit_hand = [getattr(self, f"LEHandadd{x}") for x in range(1, 6)]
        msg = UI_LANGUAGE.generate_password_header("amount")
        for lineedit in self.lineedit_hand:
            lineedit.clicked.connect(lambda o=lineedit: self.mainscreen.passwordwindow(o, 400, 50, msg))
            lineedit.setValidator(QIntValidator(0, 300))
            lineedit.setMaxLength(3)
        self.fill_elements()
        self.move(0, 100)
        UI_LANGUAGE.adjust_handadds_window(self)

    def fill_elements(self):
        for i, row in enumerate(shared.handaddlist, start=1):
            ingredient_name = DB_COMMANDER.get_ingredient_name_from_id(row[0])
            combobox = getattr(self, f"CBHandadd{i}")
            lineedit = getattr(self, f"LEHandadd{i}")
            DP_CONTROLLER.set_combobox_item(combobox, ingredient_name)
            lineedit.setText(str(row[1]))

    def abbrechen_clicked(self):
        """ Closes the window without any action. """
        self.close()

    def eintragen_clicked(self):
        """ Closes the window and enters the values into the DB/LE. """
        ingredient_list, amount_list, error = self.build_list_pairs()
        if error:
            DP_CONTROLLER.say_some_value_missing()
            return
        # check if any ingredient was used twice
        counted_ingredients = Counter(ingredient_list)
        double_ingredient = [x[0] for x in counted_ingredients.items() if x[1] > 1]
        if len(double_ingredient) != 0:
            DP_CONTROLLER.say_ingredient_double_usage(double_ingredient[0])
            return
        # if it passes all tests, generate the list for the later entry ands enter the comment into the according field
        shared.handaddlist = []
        commenttext = ""
        for ingredient, amount in zip(ingredient_list, amount_list):
            ingredient_data = DB_COMMANDER.get_ingredient_data(ingredient)
            alcoholic = 1 if ingredient_data["alcohollevel"] > 0 else 0
            shared.handaddlist.append(
                [ingredient_data["ID"], amount, alcoholic, 1, ingredient_data["alcohollevel"]])
            commenttext += f"{amount} ml {ingredient}, "
        commenttext = commenttext[:-2]
        self.mainscreen.LEKommentar.setText(commenttext)
        self.close()

    def missing_pairs(self, combobox, lineedit):
        if ((combobox.currentText() != "") and lineedit.text() == "") or ((combobox.currentText() == "") and lineedit.text() != ""):
            return True
        return False

    def build_list_pairs(self):
        ingredient_list = []
        amount_list = []
        # checks for each row if both values are nothing or a value (you need both for a valid entry)
        for i in range(1, 6):
            lineedit = getattr(self, f"LEHandadd{i}")
            combobox = getattr(self, f"CBHandadd{i}")
            if self.missing_pairs(combobox, lineedit):
                return [], [], True
            # append both values to the lists
            if combobox.currentText() != "":
                ingredient_list.append(combobox.currentText())
                amount_list.append(int(lineedit.text()))
        return ingredient_list, amount_list, False
