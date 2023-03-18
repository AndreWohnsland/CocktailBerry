from typing import get_args
from dataclasses import fields
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel
from PyQt5.QtGui import QFont

from src import SupportedThemesType
from src.ui.icons import parse_colors
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements import Ui_ColorWindow
from src.ui_elements.clickablelineedit import ClickableLineEdit

THEMES = list(get_args(SupportedThemesType))
SMALL_FONT = 12
MEDIUM_FONT = 14
LARGE_FONT = 16


class ColorWindow(QMainWindow, Ui_ColorWindow):
    """ Creates the log window Widget. """

    def __init__(self, parent):
        """ Init. Connect all the buttons and set window policy. """
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)
        self.button_use_template.clicked.connect(self._set_selected_template)

        # Get log file names, fill widget, select default, if it exists
        DP_CONTROLLER.fill_single_combobox(self.selection_template, THEMES, first_empty=False)
        self._generate_color_fields()

        UI_LANGUAGE.adjust_color_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _set_selected_template(self):
        """Uses the selected template and fills the color into the fields"""
        template: SupportedThemesType = self.selection_template.currentText()  # type: ignore -> only these are set
        colors = parse_colors(template)
        print(colors)

    def _generate_color_fields(self):
        """Generates all the needed fields to change colors"""
        self.custom_colors = parse_colors("custom")
        self.inputs_colors: dict[str, ClickableLineEdit] = {}
        for color in fields(self.custom_colors):
            self._generate_color_section(color.name)

    def _generate_color_section(self, color_name: str):
        header = QLabel(f"{color_name}:")
        self._adjust_font(header, LARGE_FONT, True)
        self.color_container.addWidget(header)
        description_text = UI_LANGUAGE.get_config_description(color_name, "color_window")
        if description_text:
            description = QLabel(description_text)
            self._adjust_font(description, SMALL_FONT)
            self.color_container.addWidget(description)
        # Reads out the current config value
        current_value = self.custom_colors[color_name]
        color_input = ClickableLineEdit(str(current_value))
        self._adjust_font(color_input, MEDIUM_FONT)
        color_input.setProperty("cssClass", "secondary")
        color_input.clicked.connect(lambda: print("TODO"))  # type: ignore
        self.color_container.addWidget(color_input)
        self.inputs_colors[color_name] = color_input

    def _adjust_font(self, element: QWidget, font_size: int, bold: bool = False):
        font = QFont()
        font.setPointSize(font_size)
        font.setBold(bold)
        weight = 75 if bold else 50
        font.setWeight(weight)
        element.setFont(font)
