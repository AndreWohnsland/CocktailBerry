import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import *


class DisplayHandler:
    """Handler Class to set/remove elements from to UI """

    def __init__(self):
        pass

    def standard_box(self, textstring):
        """ The default messagebox for the Maker. Uses a QMessageBox with OK-Button """
        msgBox = QMessageBox()
        msgBox.setStandardButtons(QMessageBox.Ok)
        buttonok = msgBox.button(QMessageBox.Ok)
        buttonok.setText("     OK     ")
        fillstring = "-" * 70
        msgBox.setText(f"{fillstring}\n{textstring}\n{fillstring}")
        msgBox.setStyleSheet(
            "QMessageBox QPushButton{background-color: rgb(0, 123, 255); color: rgb(0, 0, 0); font-size: 30pt;} QMessageBox{background-color: rgb(10, 10, 10); font-size: 16pt;} QMessageBox QLabel{color: rgb(0, 123, 255);}"
        )
        msgBox.showFullScreen()
        msgBox.exec_()

    # LineEdit
    def clean_multiple_lineedit(self, lineedit_list):
        for lineedit in lineedit_list:
            lineedit.setText("")

    def fill_multiple_lineedit(self, lineedit_list, text_list):
        for lineedit, text in zip(lineedit_list, text_list):
            lineedit.setText(text)

    # Combobox
    def fill_single_combobox(self, combobox, itemlist, clear_first=False):
        if clear_first:
            combobox.clear()
        if combobox.count() == 0:
            combobox.addItem("")
        combobox.addItems(itemlist)

    def fill_multiple_combobox(self, combobox_list, itemlist, clear_first=False):
        for combobox in combobox_list:
            self.fill_single_combobox(combobox, itemlist, clear_first)

    def fill_multiple_combobox_individually(self, combobox_list, list_of_itemlist, clear_first=False):
        for combobox, itemlist in zip(combobox_list, list_of_itemlist):
            self.fill_single_combobox(combobox, itemlist, clear_first)

    def delete_single_combobox_item(self, combobox, item):
        index = combobox.findText(item, Qt.MatchFixedString)
        if index >= 0:
            combobox.removeItem(index)

    def delete_multiple_combobox_item(self, combobox, itemlist):
        for item in itemlist:
            self.delete_single_combobox_item(combobox, item)

    def delete_item_in_multiple_combobox(self, combobox_list, item):
        for combobox in combobox_list:
            self.delete_single_combobox_item(combobox, item)

    def sort_multiple_combobox(self, combobox_list):
        for combobox in combobox_list:
            combobox.sort()

    def set_multiple_combobox_items(self, combobox_list, item_to_set):
        for combobox, item in zip(combobox_list, item_to_set):
            index = combobox.findText(item, Qt.MatchFixedString)
            combobox.setCurrentIndex(index)

    def adjust_bottle_comboboxes(self, combobox_list, old_item, new_item):
        for combobox in combobox_list:
            if (old_item != "") and (new_item != combobox.currentText()):
                combobox.addItem(old_item)
            if (new_item != "") and (new_item != combobox.currentText()):
                self.delete_single_combobox_item(combobox, new_item)
            combobox.model().sort(0)

    # buttons / togglebuttons
    def untoggle_buttons(self, button_list):
        for button in button_list:
            button.setChecked(False)

    # progress bars
    def set_progress_bar_values(self, progress_bar_list, value_list):
        for progress_bar, value in zip(progress_bar_list, value_list):
            progress_bar.setValue(value)
