from typing import Literal
from PyQt5.QtWidgets import QDialog
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.config_manager import CONFIG as cfg
from src.ui_elements.passworddialog import Ui_PasswordDialog


class PasswordDialog(QDialog, Ui_PasswordDialog):
    """ Creates the Password Widget. """

    def __init__(
        self,
        right_password: int = cfg.UI_MASTERPASSWORD,
        header_type: Literal['master', 'maker'] = "master"
    ):
        """ Init. Connect all the buttons and set window policy. """
        super().__init__()
        self.setupUi(self)
        self.right_password = right_password
        DP_CONTROLLER.initialize_window_object(self)
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.enter_button.clicked.connect(self.enter_clicked)
        self.cancel_button.clicked.connect(self._cancel_clicked)
        self.PBdel.clicked.connect(self.del_clicked)
        self.number_list = list(range(10))
        self.attribute_numbers = [getattr(self, "PB" + str(x)) for x in self.number_list]
        for obj, number in zip(self.attribute_numbers, self.number_list):
            obj.clicked.connect(lambda _, n=number: self.number_clicked(number=n))
        UI_LANGUAGE.adjust_password_window(self, header_type)
        DP_CONTROLLER.set_display_settings(self)

    def number_clicked(self, number: int):
        """  Adds the clicked number to the lineedit. """
        self.password_field.setText(f"{self.password_field.text()}{number}")

    def enter_clicked(self):
        """ Enters/Closes the Dialog. """
        password_string = self.password_field.text()
        password = 0 if len(password_string) == 0 else int(password_string)
        if self.right_password == password:
            self.accept()
            return
        DP_CONTROLLER.say_wrong_password()
        self.password_field.clear()

    def _cancel_clicked(self):
        """Cancel the password confirmation an aborts process"""
        self.reject()

    def del_clicked(self):
        """ Deletes the last digit in the lineedit. """
        current_string = self.password_field.text()
        self.password_field.setText(current_string[:-1])
