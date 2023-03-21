from collections import Counter

from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QIntValidator
from src.models import Ingredient

from src.ui_elements.handadds import Ui_Handadds
from src.display_controller import DP_CONTROLLER
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.config_manager import shared


class HandaddWidget(QDialog, Ui_Handadds):
    """ Creates a window where the user can define additional ingredients to add via hand after the machine. """

    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self, 20, 100)
        self.mainscreen = parent
        # generating a sorted by name list for all ingredients, all handadd first
        hand_ingredients = DB_COMMANDER.get_all_ingredients(get_machine=False)
        machine_ingredients = DB_COMMANDER.get_all_ingredients(get_hand=False)
        hand_list = sorted([x.name for x in hand_ingredients])
        machine_list = sorted([x.name for x in machine_ingredients])
        ingredient_list = hand_list + machine_list
        self.comboboxes_handadd = [getattr(self, f"CBHandadd{x}") for x in range(1, 6)]
        DP_CONTROLLER.fill_multiple_combobox(self.comboboxes_handadd, ingredient_list, sort_items=False)
        # connect the buttons
        self.PBAbbrechen.clicked.connect(self._cancel_clicked)
        self.PBEintragen.clicked.connect(self._enter_clicked)

        self.lineedit_hand = [getattr(self, f"LEHandadd{x}") for x in range(1, 6)]
        msg = UI_LANGUAGE.generate_numpad_header("amount")
        for lineedit in self.lineedit_hand:
            lineedit.clicked.connect(lambda o=lineedit: self.mainscreen.open_numpad(o, 400, 50, msg))
            lineedit.setValidator(QIntValidator(0, 300))
            lineedit.setMaxLength(3)
        self.fill_elements()
        UI_LANGUAGE.adjust_handadds_window(self)
        self.show()
        DP_CONTROLLER.set_display_settings(self, resize=False)

    def fill_elements(self):
        for i, ing in enumerate(shared.handaddlist, start=1):
            combobox = getattr(self, f"CBHandadd{i}")
            lineedit = getattr(self, f"LEHandadd{i}")
            DP_CONTROLLER.set_combobox_item(combobox, ing.name)
            lineedit.setText(str(ing.amount))

    def _cancel_clicked(self):
        """ Closes the window without any action. """
        self.close()

    def _enter_clicked(self):
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
        comment_text = ""
        for ingredient_name, amount in zip(ingredient_list, amount_list):
            ingredient: Ingredient = DB_COMMANDER.get_ingredient(ingredient_name)  # type: ignore
            ingredient.amount = amount
            ingredient.recipe_hand = True
            shared.handaddlist.append(ingredient)
            comment_text += f"{amount} ml {ingredient_name}, "
        comment_text = comment_text[:-2]
        self.mainscreen.LEKommentar.setText(comment_text)
        self.close()

    def missing_pairs(self, combobox, lineedit):
        if (
            ((combobox.currentText() != "") and lineedit.text() == "")
            or
            ((combobox.currentText() == "") and lineedit.text() != "")
        ):
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
