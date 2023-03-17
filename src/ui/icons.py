from typing import Literal, Optional
from dataclasses import dataclass
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
import qtawesome as qta

from src import SupportedThemesType
from src.filepath import STYLE_FOLDER
from src.config_manager import CONFIG as cfg

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


@dataclass
class ColorInformation:
    primary: str
    secondary: str
    destructive: str
    neutral: str
    background: str
    border: str
    progressbar: str
    progressbg: str
    tabborder: str


def parse_colors(theme: Optional[SupportedThemesType] = None) -> ColorInformation:
    """Gets the color out of the theme file"""
    # extract all the fields as list from the dataclass
    needed_fields = list(ColorInformation.__dict__["__dataclass_fields__"].keys())
    extracted = {}
    # if no theme arg is provided, get the theme defined by settings
    if theme is None:
        theme = cfg.MAKER_THEME
    ui_file = STYLE_FOLDER / f"{theme}.scss"
    content = ui_file.read_text().split("\n")
    for line in content:
        name, *color_info = line.split(": ")
        # remove dollar variable sign before the name
        name = name.replace("$", "")
        # check if or which list element match, if match assign the color
        found = [ele for ele in needed_fields if ele == name]
        if found:
            extracted[found[0]] = color_info[0].replace(";", "")
    # If any color is missing, assign default color
    default_color = "#007bff"
    for field in needed_fields:
        if field not in extracted:
            extracted[field] = default_color
    return ColorInformation(**extracted)


class IconSetter:
    def __init__(self):
        self.color = parse_colors()

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
            icon = qta.icon(icon, color=self.color.background)
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
        w.PBMminus.setIcon(qta.icon(_MINUS_ICON, color=self.color.primary))
        w.PBMminus.setIconSize(_BUTTON_SIZE)
        w.PBMminus.setText("")
        w.PBMplus.setIcon(qta.icon(_PLUS_ICON, color=self.color.primary))
        w.PBMplus.setIconSize(_BUTTON_SIZE)
        w.PBMplus.setText("")

    def set_wait_icon(self, button: QPushButton, icon: Literal["spin", "time"] = "time", primary=False):
        """Sets a spinner button to the icon"""
        color = self.color.primary if primary else self.color.background
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
        # Removes the previous set "padding"
        button.setText(button.text().strip())
        button.setIcon(QIcon())


ICONS = IconSetter()
