from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from ui_elements.passwordbuttons2 import Ui_PasswordWindow2


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
        if not self.ms.DEVENVIRONMENT:
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
