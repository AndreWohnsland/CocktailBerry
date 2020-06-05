import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *


class DisplayControler:
    def __init__(self):
        pass

    def get_current_combobox_items(self, combobox_list):
        items = []
        for combobox in combobox_list:
            items.append(combobox.currentText())
        return items
