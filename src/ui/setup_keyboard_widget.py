import string
from PyQt5.QtWidgets import QDialog, QLineEdit
from PyQt5.QtCore import Qt

from src.display_controller import DP_CONTROLLER
from src.ui_elements.keyboard import Ui_Keyboard


class KeyboardWidget(QDialog, Ui_Keyboard):
    """ Creates a keyboard where the user can enter names or similar strings to Lineedits. """

    def __init__(self, parent, le_to_write: QLineEdit, max_char_len: int = 30):
        super().__init__()
        self.setupUi(self)
        self.mainscreen = parent
        self.le_to_write = le_to_write
        self.LName.setText(self.le_to_write.text())
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        # populating all the buttons
        self.backButton.clicked.connect(self.back_button_clicked)
        self.clear.clicked.connect(self.clear_button_clicked)
        self.enterButton.clicked.connect(self.enter_button_clicked)
        self.space.clicked.connect(lambda: self.input_button_clicked(" ", " "))
        self.delButton.clicked.connect(self.delete_clicked)
        self.shift.clicked.connect(self.shift_clicked)
        # generating the lists to populate all remaining buttons via iteration
        self.number_list = list(range(10))
        # also gives the possibility to use some extra signs
        self.sign_list = [".", ":", "/", "#", "'", '"', "-", "_", "(", ")"]
        self.char_list_lower = list(string.ascii_lowercase)
        self.char_list_upper = list(string.ascii_uppercase)
        self.attribute_chars = [getattr(self, f"Button{x}") for x in self.char_list_lower]
        self.attribute_numbers = [getattr(self, f"Button{x}") for x in self.number_list]
        for obj, char, char2 in zip(self.attribute_chars, self.char_list_lower, self.char_list_upper):
            obj.clicked.connect(lambda _, iv=char, iv_s=char2: self.input_button_clicked(
                input_value=iv, input_value_shift=iv_s))
        for obj, char, char2 in zip(self.attribute_numbers, self.number_list, self.sign_list):
            obj.clicked.connect(lambda _, iv=char, iv_s=char2: self.input_button_clicked(
                input_value=iv, input_value_shift=iv_s))
        # restricting the Lineedit to a set up Char length
        self.LName.setMaxLength(max_char_len)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def back_button_clicked(self):
        """ Closes the Window without any further action. """
        self.close()

    def clear_button_clicked(self):
        """ Clears the input. """
        self.LName.setText("")

    def enter_button_clicked(self):
        """ Closes and enters the String value back to the Lineedit. """
        self.le_to_write.setText(self.LName.text())
        self.close()

    def input_button_clicked(self, input_value: str, input_value_shift: str):
        """ Enters the input_value into the field, adds it to the string.
        Can either have the normal or the shift value, if there is no difference both input arguments are the same.
        """
        string_value = self.LName.text()
        if self.shift.isChecked():
            add_value = input_value_shift
        else:
            add_value = input_value
        string_value += str(add_value)
        self.LName.setText(string_value)

    def delete_clicked(self):
        string_value = self.LName.text()
        self.LName.setText(string_value[:-1])

    def shift_clicked(self):
        if self.shift.isChecked():
            char_choose = self.char_list_upper
            number_choose = self.sign_list
        else:
            char_choose = self.char_list_lower
            number_choose = self.number_list
        for obj, char in zip(self.attribute_chars, char_choose):
            obj.setText(str(char))
        for obj, char in zip(self.attribute_numbers, number_choose):
            obj.setText(str(char))
