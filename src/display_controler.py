import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from config.config_manager import ConfigManager


class DisplayControler(ConfigManager):
    """ Controler Class to get Values from the UI"""

    def __init__(self):
        pass

    def get_current_combobox_items(self, combobox_list):
        items = []
        for combobox in combobox_list:
            items.append(combobox.currentText())
        return items

    def get_toggle_status(self, button_list):
        checked = []
        for button in button_list:
            if button.isChecked():
                checked.append(True)
            else:
                checked.append(False)
        return checked

    def check_password(self, lineedit):
        password = lineedit.text()
        lineedit.setText("")
        if password == self.masterpassword:
            return True
        return False
