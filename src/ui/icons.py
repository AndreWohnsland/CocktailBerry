from pathlib import Path
from PyQt5.QtCore import QSize
import qtawesome as qta

from src.config_manager import CONFIG as cfg

DIRPATH = Path(__file__).parent.absolute()
UI_FILE = DIRPATH / "styles" / f"{cfg.MAKER_THEME}.scss"

# DEFINING THE ICONS
_SETTING_ICON = "fa5s.cog"
_PLUS_ICON = "fa5s.plus"
_MINUS_ICON = "fa5s.minus"
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
        self.background = _parse_color("background")

    def set_mainwindow_icons(self, w):
        """Sets the icons of the main window according to style sheets props"""
        w.option_button.setIcon(qta.icon(_SETTING_ICON, color=self.background))
        w.option_button.setIconSize(_BUTTON_SIZE)

    def _set_plus_minus_mw_experimental(self, w):
        w.PBMminus.setIcon(qta.icon(_MINUS_ICON, color=self.primary_color))
        w.PBMminus.setIconSize(_BUTTON_SIZE)
        w.PBMminus.setText("")
        w.PBMplus.setIcon(qta.icon(_PLUS_ICON, color=self.primary_color))
        w.PBMplus.setIconSize(_BUTTON_SIZE)
        w.PBMplus.setText("")


ICONS = IconSetter()
