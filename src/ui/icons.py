from pathlib import Path
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
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
        # For solid buttons
        for ui_element, icon in [
            (w.option_button, _SETTING_ICON),
            (w.PBZdelete, _DELETE_ICON),
            (w.PBdelete, _DELETE_ICON),
            (w.PBZclear, _CLEAR_ICON),
            (w.PBclear, _CLEAR_ICON),
        ]:
            self._set_icon(ui_element, qta.icon(icon, color=self.background))
        # For outline buttons
        for ui_element, icon, color in [
        ]:
            self._set_icon(ui_element, qta.icon(icon, color=color))

    def _set_icon(self, ui_element: QPushButton, icon):
        ui_element.setIcon(icon)
        ui_element.setIconSize(_BUTTON_SIZE)
        ui_element.setText("")

    def _set_plus_minus_mw_experimental(self, w):
        w.PBMminus.setIcon(qta.icon(_MINUS_ICON, color=self.primary_color))
        w.PBMminus.setIconSize(_BUTTON_SIZE)
        w.PBMminus.setText("")
        w.PBMplus.setIcon(qta.icon(_PLUS_ICON, color=self.primary_color))
        w.PBMplus.setIconSize(_BUTTON_SIZE)
        w.PBMplus.setText("")


ICONS = IconSetter()
