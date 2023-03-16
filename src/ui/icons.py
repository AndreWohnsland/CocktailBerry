from pathlib import Path
from typing import Literal
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
import qtawesome as qta

from src.config_manager import CONFIG as cfg

DIRPATH = Path(__file__).parent.absolute()
UI_FILE = DIRPATH / "styles" / f"{cfg.MAKER_THEME}.scss"

# DEFINING THE ICONS
_SETTING_ICON = "fa5s.cog"
_PLUS_ICON = "fa5s.plus"
_MINUS_ICON = "fa5s.minus"
_DELETE_ICON = "fa5s.trash-alt"
_CLEAR_ICON = "fa5s.eraser"
_COCKTAIL_ICON = "fa5s.cocktail"
_SPINNER_ICON = "fa5s.spinner"
_TIME_ICON = "fa5s.hourglass-start"
_BUTTON_SIZE = QSize(36, 36)


def _parse_color(color_name: str) -> str:
    """Gets the color out of the theme file"""
    default_color = "#007bff"
    content = UI_FILE.read_text().split("\n")
    for line in content:
        name, *color_info = line.split(": ")
        if color_name in name:
            return color_info[0].replace(";", "")
    return default_color


class IconSetter:
    def __init__(self):
        self.primary_color = _parse_color("primary")
        self.secondary_color = _parse_color("secondary")
        self.neutral_color = _parse_color("neutral")
        self.destructive_color = _parse_color("destructive")
        self.background = _parse_color("background")

    def set_mainwindow_icons(self, w):
        """Sets the icons of the main window according to style sheets props"""
        # For solid buttons, they use bg color for icon
        for ui_element, icon, no_text in [
            (w.option_button, _SETTING_ICON, True),
            (w.PBZdelete, _DELETE_ICON, True),
            (w.PBdelete, _DELETE_ICON, True),
            (w.PBZclear, _CLEAR_ICON, True),
            (w.PBclear, _CLEAR_ICON, True),
            (w.prepare_button, _COCKTAIL_ICON, False),
        ]:
            icon = qta.icon(icon, color=self.background)
            self._set_icon(ui_element, icon, no_text)
        # For outline buttons, they use button color for icon
        for ui_element, icon, color, no_text in [
        ]:
            self._set_icon(ui_element, qta.icon(icon, color=color), no_text)

    def _set_icon(self, ui_element: QPushButton, icon, no_text: bool):
        ui_element.setIcon(icon)
        ui_element.setIconSize(_BUTTON_SIZE)
        if no_text:
            ui_element.setText("")

    def _set_plus_minus_mw_experimental(self, w):
        w.PBMminus.setIcon(qta.icon(_MINUS_ICON, color=self.primary_color))
        w.PBMminus.setIconSize(_BUTTON_SIZE)
        w.PBMminus.setText("")
        w.PBMplus.setIcon(qta.icon(_PLUS_ICON, color=self.primary_color))
        w.PBMplus.setIconSize(_BUTTON_SIZE)
        w.PBMplus.setText("")

    def set_wait_icon(self, button: QPushButton, icon: Literal["spin", "time"] = "time", primary=False):
        """Sets a spinner button to the icon"""
        color = self.primary_color if primary else self.background
        if icon == "spin":
            used_icon = qta.icon(_SPINNER_ICON, color=color, animation=qta.Spin(button))
        else:
            used_icon = qta.icon(_TIME_ICON, color=color)
        # add "padding" in front of button
        button.setText(f" {button.text()}")
        button.setIconSize(_BUTTON_SIZE)
        button.setIcon(used_icon)  # type: ignore

    def remove_icon(self, button: QPushButton):
        """Removes the spinner from the button"""
        button.setText(button.text().strip())
        button.setIcon(QIcon())


ICONS = IconSetter()
