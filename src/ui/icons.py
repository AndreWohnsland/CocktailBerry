from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import qtawesome as qta
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QPushButton, QWidget
from pyqtspinner import WaitingSpinner

from src import SupportedThemesType
from src.config.config_manager import CONFIG as cfg
from src.filepath import STYLE_FOLDER

if TYPE_CHECKING:
    from src.ui_elements import Ui_CocktailSelection, Ui_MainWindow, Ui_PictureWindow

# DEFINING THE ICONS
_SETTING_ICON = "fa5s.cog"
_PLUS_ICON = "fa5s.plus"
_MINUS_ICON = "fa5s.minus"
_DELETE_ICON = "fa5s.trash-alt"
_CLEAR_ICON = "fa5s.eraser"
_COCKTAIL_ICON = "fa5s.cocktail"
_HUGE_GLASS = "mdi.glass-mug"
_BIG_GLASS = "mdi.glass-pint-outline"
_MEDIUM_GLASS = "mdi.glass-cocktail"
_SMALL_GLASS = "mdi.glass-tulip"
_TINY_GLASS = "mdi.glass-flute"
_SKULL = "fa5s.skull-crossbones"
_EASY = "mdi.emoticon-excited"
_VIRGIN_ICON = "mdi.glass-cocktail-off"
_SPINNER_ICON = "fa5s.spinner"
_TIME_ICON = "fa5s.hourglass-start"
_SEARCH_ICON = "fa.search"
_UPLOAD_ICON = "fa.upload"
_QUESTION_ICON = "fa5.question-circle"
_BORDER_ICON = "fa5.square"
BUTTON_SIZE = QSize(36, 36)
SMALL_BUTTON_SIZE = QSize(24, 24)


@dataclass
class PresetIcon:
    setting = _SETTING_ICON
    plus = _PLUS_ICON
    minus = _MINUS_ICON
    delete = _DELETE_ICON
    clear = _CLEAR_ICON
    cocktail = _COCKTAIL_ICON
    virgin = _VIRGIN_ICON
    spinner = _SPINNER_ICON
    time = _TIME_ICON
    search = _SEARCH_ICON
    upload = _UPLOAD_ICON
    question = _QUESTION_ICON
    tiny_glass = _TINY_GLASS
    small_glass = _SMALL_GLASS
    medium_glass = _MEDIUM_GLASS
    big_glass = _BIG_GLASS
    huge_glass = _HUGE_GLASS
    skull = _SKULL
    easy = _EASY
    border = _BORDER_ICON


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

    def __getitem__(self, item):
        return getattr(self, item)


def parse_colors(theme: SupportedThemesType | None = None) -> ColorInformation:
    """Get the color out of the theme file."""
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
        self.presets = PresetIcon()
        self._spinner: WaitingSpinner | None = None

    def set_mainwindow_icons(self, w: Ui_MainWindow):
        """Set the icons of the main window according to style sheets props."""
        # For solid buttons, they use bg color for icon
        for ui_element, icon, no_text in [
            (w.option_button, _SETTING_ICON, True),
            (w.PBZdelete, _DELETE_ICON, True),
            (w.PBdelete, _DELETE_ICON, True),
            (w.PBZclear, _CLEAR_ICON, True),
            (w.PBclear, _CLEAR_ICON, True),
        ]:
            fa_icon: QIcon = qta.icon(icon, color=self.color.background)
            self.set_icon(ui_element, fa_icon, no_text)
        # using smaller button size here
        self.set_icon(
            w.button_info_recipes,
            qta.icon(_QUESTION_ICON, color=self.color.background),
            True,
            SMALL_BUTTON_SIZE,
        )
        # also set tab
        w.tabWidget.setTabIcon(0, qta.icon(_SEARCH_ICON, color=self.color.background))
        w.tabWidget.setIconSize(SMALL_BUTTON_SIZE)
        w.tabWidget.setTabText(0, "")

    def set_cocktail_selection_icons(self, w: Ui_CocktailSelection):
        """Set the icons of the cocktail selection window according to style sheets props."""
        for ui_element, icon, no_text in [
            (w.prepare_button, _COCKTAIL_ICON, False),
            (w.increase_alcohol, _SKULL, True),
            (w.decrease_alcohol, _EASY, True),
        ]:
            fa_icon: QIcon = qta.icon(icon, color=self.color.background)
            self.set_icon(ui_element, fa_icon, no_text)

    def set_icon(self, ui_element: QPushButton, icon: QIcon, no_text: bool, size: QSize = BUTTON_SIZE):
        """Set the icon of the given ui element."""
        ui_element.setIcon(icon)
        ui_element.setIconSize(size)
        if no_text:
            ui_element.setText("")

    def set_picture_window_icons(self, w: Ui_PictureWindow):
        for ui_element, icon, no_text in [
            (w.button_upload, _UPLOAD_ICON, True),
            (w.button_remove, _DELETE_ICON, True),
        ]:
            fa_icon: QIcon = qta.icon(icon, color=self.color.background)
            self.set_icon(ui_element, fa_icon, no_text)

    def generate_icon(self, icon_name: str, color: str, color_active: str | None = None, border: bool = False) -> QIcon:
        """Generate an icon with the given color and size.

        Args:
        ----
            icon_name (str): icon name in qta, e.g. "fa5s.cog"
            color (str): given color name in hex, e.g. "#007bff"
            color_active (str): given active color name, will use color if None, defaults to None
            border (bool): if True, add a border to the icon, defaults to False

        """
        icon_option: dict[str, Any] = {
            "color": color,
            "color_active": color if color_active is None else color_active,
        }
        if not border:
            return qta.icon(icon_name, options=[icon_option])
        return qta.icon(
            icon_name,
            _BORDER_ICON,
            options=[icon_option, {**icon_option, "scale_factor": 1.3}],
        )

    def set_wait_icon(self, button: QPushButton, icon: Literal["spin", "time"] = "time", primary=False):
        """Set a spinner button to the icon."""
        color = self.color.primary if primary else self.color.background
        if icon == "spin":
            used_icon = qta.icon(_SPINNER_ICON, color=color, animation=qta.Spin(button))
        else:
            used_icon = qta.icon(_TIME_ICON, color=color)
        # add "padding" in front of button
        button.setText(f" {button.text()}")
        button.setIconSize(BUTTON_SIZE)
        button.setIcon(used_icon)  # type: ignore

    def remove_icon(self, button: QPushButton):
        """Remove the spinner from the button."""
        # Removes the previous set "padding"
        button.setText(button.text().strip())
        button.setIcon(QIcon())

    def start_spinner(self, parent_widget: QWidget):
        """Start a spinner above the parent widget, locks parent."""
        self._spinner = WaitingSpinner(
            parent_widget,
            disable_parent_when_spinning=True,
            roundness=99.9,
            fade=90.0,
            radius=50,
            lines=8,
            line_length=80,
            line_width=60,
            speed=1.0,
            color=QColor(self.color.primary),
        )
        self._spinner.start()

    def stop_spinner(self):
        """Stop the spinner."""
        if self._spinner is None:
            return
        self._spinner.stop()


ICONS = IconSetter()
