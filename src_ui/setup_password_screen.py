from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog

from src.display_controller import DP_CONTROLLER
from ui_elements.passwordbuttons2 import Ui_PasswordWindow2


class PasswordScreen(QDialog, Ui_PasswordWindow2):
    """ Creates the Passwordscreen. """

    def __init__(self, parent, x_pos=0, y_pos=0, le_to_write=None, headertext="Password"):
        """ Init. Connect all the buttons and set window policy. """
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon(parent.icon_path))
        # Connect all the buttons, generates a list of the numbers an objectnames to do that
        self.PBenter.clicked.connect(self.enter_clicked)
        self.PBdel.clicked.connect(self.del_clicked)
        self.number_list = list(range(10))
        self.attribute_numbers = [getattr(self, "PB" + str(x)) for x in self.number_list]
        for obj, number in zip(self.attribute_numbers, self.number_list):
            obj.clicked.connect(lambda _, n=number: self.number_clicked(number=n))
        self.mainscreen = parent
        self.setWindowTitle(headertext)
        self.LHeader.setText(headertext)
        self.pwlineedit = le_to_write
        self.move(x_pos, y_pos)
        self.show()
        DP_CONTROLLER.set_dev_settings(self, resize=False)

    def number_clicked(self, number):
        """  Adds the clicked number to the lineedit. """
        self.pwlineedit.setText(f"{self.pwlineedit.text()}{number}")

    def enter_clicked(self):
        """ Enters/Closes the Dialog. """
        self.close()

    def del_clicked(self):
        """ Deletes the last digit in the lineedit. """
        strstor = self.pwlineedit.text()
        self.pwlineedit.setText(strstor[:-1])
