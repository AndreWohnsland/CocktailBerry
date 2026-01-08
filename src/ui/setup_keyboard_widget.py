from __future__ import annotations

import string
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QLineEdit, QMainWindow

from src.display_controller import DP_CONTROLLER
from src.ui_elements.keyboard import Ui_Keyboard

if TYPE_CHECKING:
    from src.ui.create_config_window import ConfigWindow
    from src.ui.setup_mainwindow import MainScreen


class KeyboardWidget(QMainWindow, Ui_Keyboard):
    """Creates a keyboard where the user can enter names or similar strings to Lineedits."""

    def __init__(self, parent: MainScreen | ConfigWindow, le_to_write: QLineEdit, max_char_len: int = 30) -> None:
        super().__init__()
        self.setupUi(self)
        self.mainscreen = parent
        self.le_to_write = le_to_write
        self.LName.setText(self.le_to_write.text())
        DP_CONTROLLER.initialize_window_object(self)
        # populating all the buttons
        self.backButton.clicked.connect(self.back_button_clicked)
        self.clear.clicked.connect(self.clear_button_clicked)
        self.enterButton.clicked.connect(self.enter_button_clicked)
        self.space.clicked.connect(lambda: self.input_button_clicked(" ", " ", " "))
        self.delButton.clicked.connect(self.delete_clicked)
        self.shift.clicked.connect(self._shift_control_clicked)
        self.button_control.clicked.connect(self._shift_control_clicked)
        # generating the lists to populate all remaining buttons via iteration
        self.number_list = list(range(10))
        # also gives the possibility to use some extra signs
        self.sign_list = ["!", '"', "§", "%", "&", "/", "(", ")", "=", "?"]
        self.sign_list_chars = [
            "^",
            "°",
            "{",
            "[",
            "]",
            "}",
            "\\",
            "`",
            "´",  # noqa: RUF001
            "#",
            "*",
            "+",
            "~",
            "ä",
            "ö",
            "ü",
            "-",
            "_",
            ":",
            ".",
            ",",
            ";",
            "#",
            "@",
            "<",
            ">",
        ]
        self.char_list_lower = list(string.ascii_lowercase)
        self.char_list_upper = list(string.ascii_uppercase)
        self.attribute_chars = [getattr(self, f"Button{x}") for x in self.char_list_lower]
        self.attribute_numbers = [getattr(self, f"Button{x}") for x in self.number_list]
        self.input_button_list = self.attribute_chars + self.attribute_numbers
        self.button_value_default_list = self.char_list_lower + self.number_list
        self.button_value_shift_list = self.char_list_upper + self.number_list
        self.button_value_control_list = self.sign_list_chars + self.sign_list
        for obj, char, char2, char3 in zip(
            self.input_button_list,
            self.button_value_default_list,
            self.button_value_shift_list,
            self.button_value_control_list,
        ):
            obj.clicked.connect(lambda _, iv=char, iv_s=char2, iv_c=char3: self.input_button_clicked(iv, iv_s, iv_c))
        # restricting the Lineedit to a set up Char length
        self.LName.setMaxLength(max_char_len)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def back_button_clicked(self) -> None:
        """Close the Window without any further action."""
        self.close()

    def clear_button_clicked(self) -> None:
        """Clear the input."""
        self.LName.setText("")

    def enter_button_clicked(self) -> None:
        """Close and enter the String value back to the Lineedit."""
        self.le_to_write.setText(self.LName.text())
        self.close()

    def input_button_clicked(self, input_default: str | int, input_shift: str | int, input_control: str | int) -> None:
        """Enter the input_value into the field, adds it to the string.

        Can either have the normal or the shift value, if there is no difference both input arguments are the same.
        """
        string_value = self.LName.text()
        add_value = input_default
        if self.shift.isChecked():
            add_value = input_shift
        if self.button_control.isChecked():
            add_value = input_control
        string_value += str(add_value)
        self.LName.setText(string_value)

    def delete_clicked(self) -> None:
        string_value = self.LName.text()
        self.LName.setText(string_value[:-1])

    def _shift_control_clicked(self) -> None:
        """Select the right character set for the buttons."""
        character_set: list[str | int] | list[str] = self.button_value_default_list
        # if shift is toggled, use the upper letters
        if self.shift.isChecked():
            character_set = self.button_value_shift_list
        # Control will overwrite the shift (upper / lower) setting
        if self.button_control.isChecked():
            character_set = self.button_value_control_list
        self._change_displayed_characters(character_set)

    def _change_displayed_characters(self, character_list: list) -> None:
        """Change the displayed values on the buttons."""
        for obj, char in zip(self.input_button_list, character_list):
            # fix for & sign, it needs to be a && in pyqt
            display_char = char
            if char == "&":
                display_char = "&&"
            obj.setText(str(display_char))
