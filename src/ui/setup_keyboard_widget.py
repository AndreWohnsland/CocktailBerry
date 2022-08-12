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
        self.backButton.clicked.connect(self.backbutton_clicked)
        self.clear.clicked.connect(self.clearbutton_clicked)
        self.enterButton.clicked.connect(self.enterbutton_clicked)
        self.space.clicked.connect(lambda: self.inputbutton_clicked(" ", " "))
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
            obj.clicked.connect(lambda _, iv=char, iv_s=char2: self.inputbutton_clicked(
                inputvalue=iv, inputvalue_shift=iv_s))
        for obj, char, char2 in zip(self.attribute_numbers, self.number_list, self.sign_list):
            obj.clicked.connect(lambda _, iv=char, iv_s=char2: self.inputbutton_clicked(
                inputvalue=iv, inputvalue_shift=iv_s))
        # restricting the Lineedit to a set up Char leng
        self.LName.setMaxLength(max_char_len)
        DP_CONTROLLER.set_display_settings(self)
        self.showFullScreen()

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

    def inputbutton_clicked(self, inputvalue: str, inputvalue_shift: str):
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
        self.LName.setText(stringvalue[:-1])

    def shift_clicked(self):
        if self.shift.isChecked():
            charchoose = self.char_list_upper
            numberchoose = self.sign_list
        else:
            charchoose = self.char_list_lower
            numberchoose = self.number_list
        for obj, char in zip(self.attribute_chars, charchoose):
            obj.setText(str(char))
        for obj, char in zip(self.attribute_numbers, numberchoose):
            obj.setText(str(char))
