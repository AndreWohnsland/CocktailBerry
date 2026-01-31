from __future__ import annotations

import contextlib
import importlib.util
import re
from dataclasses import fields
from typing import TYPE_CHECKING, get_args

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog, QLabel, QLineEdit, QMainWindow

from src import SupportedThemesType
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.filepath import CUSTOM_STYLE_FILE, CUSTOM_STYLE_SCSS
from src.migration.migrator import CouldNotMigrateException, Migrator
from src.ui.creation_utils import LARGE_FONT, MEDIUM_FONT, SMALL_FONT, adjust_font, create_spacer
from src.ui.icons import parse_colors
from src.ui.qt_worker import CallableWorker, run_with_spinner
from src.ui_elements import Ui_ColorWindow
from src.ui_elements.clickablelineedit import ClickableLineEdit
from src.utils import restart_v1

try:
    import qtsass

    _QTSASS_INSTALLED = True
except ModuleNotFoundError:
    _QTSASS_INSTALLED = False

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


THEMES = list(get_args(SupportedThemesType))


def _install_qtsass() -> None:
    """Install qtsass package."""
    migrator = Migrator()
    with contextlib.suppress(CouldNotMigrateException):
        migrator._install_pip_package("qtsass", "1.17.0")


class ColorWindow(QMainWindow, Ui_ColorWindow):
    """Creates the log window Widget."""

    def __init__(self, parent: None | MainScreen) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        self.color_picker: QColorDialog | None = None
        self.inputs_colors: dict[str, ClickableLineEdit] = {}
        self.custom_colors = parse_colors("custom")
        # Connect all the buttons, generates a list of the numbers an object names to do that
        self.button_back.clicked.connect(self.close)  # pyright: ignore[reportArgumentType]
        self.button_use_template.clicked.connect(self._set_selected_template)
        self.button_apply.clicked.connect(self._apply_settings)

        # Get log file names, fill widget, select default, if it exists
        DP_CONTROLLER.fill_single_combobox(self.selection_template, THEMES, first_empty=False)
        self._generate_color_fields()

        UI_LANGUAGE.adjust_color_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

        # If the module is not installed, we cannot compile.
        # The module will be only installed at a new installation but not an update
        # This is because the wheels are not build for aarch64, so it takes a LOT of time
        # Shows prompt with info, if user yes, install the package and restart
        if _QTSASS_INSTALLED:
            return
        self.button_apply.setDisabled(True)
        if DP_CONTROLLER.ask_to_install_qtsass():
            self._worker: CallableWorker[None] = run_with_spinner(
                _install_qtsass,
                parent=self,
                on_finish=lambda _: self._finish_installer_worker(),
            )

    def _set_selected_template(self) -> None:
        """Use the selected template and fills the color into the fields."""
        template: SupportedThemesType = self.selection_template.currentText()  # type: ignore
        colors = parse_colors(template)
        for color in fields(colors):
            line_edit = self.inputs_colors[color.name]
            color_value = colors[color.name]
            line_edit.setText(color_value)
            line_edit.setStyleSheet(self._generate_style(color_value))

    def _generate_color_fields(self) -> None:
        """Generate all the needed fields to change colors."""
        # adds a spacer on top
        self.color_container.addItem(create_spacer(20))
        for color in fields(self.custom_colors):
            self._generate_color_section(color.name)
            self.color_container.addItem(create_spacer(12))

    def _generate_color_section(self, color_name: str) -> None:
        """Generate a section for the color including color pad, and user input."""
        header = QLabel(f"{color_name}:")
        adjust_font(header, LARGE_FONT, True)
        self.color_container.addWidget(header)
        description_text = UI_LANGUAGE.get_config_description(color_name, "color_window")
        if description_text:
            description = QLabel(description_text)
            adjust_font(description, SMALL_FONT)
            self.color_container.addWidget(description)

        # Reads out the current config value
        current_value = self.custom_colors[color_name]
        color_input = ClickableLineEdit(str(current_value))
        color_input.setMinimumSize(QSize(0, 50))
        color_input.clicked.connect(lambda: self._connect_color_picker(color_input))
        color_input.setStyleSheet(self._generate_style(current_value))
        adjust_font(color_input, MEDIUM_FONT)
        color_input.setProperty("cssClass", "secondary")
        self.color_container.addWidget(color_input)
        self.inputs_colors[color_name] = color_input

    def _connect_color_picker(self, line_edit_to_write: QLineEdit) -> None:
        """Open a color picker for the user to select the color.

        Uses the current color as default.
        Inserts the selected color into the line edit.
        """
        self.color_picker = QColorDialog(self)
        current_color = line_edit_to_write.text()
        self.color_picker.setCurrentColor(QColor(current_color))
        # self.color_picker.showFullScreen()
        self.color_picker.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        if self.color_picker.exec():
            selected_color = self.color_picker.currentColor().name()
            line_edit_to_write.setText(selected_color)
            line_edit_to_write.setStyleSheet(self._generate_style(selected_color))

    def _generate_style(self, color: str) -> str:
        """Generate a style with same bg and font color."""
        return f"background-color: {color}; color: {color};"

    def _apply_settings(self) -> None:
        """Apply the settings to the custom.scss file.

        Builds the css file afterwards with the qtsass package.
        """
        # read in the custom style file
        style = CUSTOM_STYLE_SCSS.read_text()

        # replace lines with new color
        for color_name, color_line_edit in self.inputs_colors.items():
            color_value: str = color_line_edit.text()
            replace_regex = r"\$" + f"{color_name}:" + r"\s*(#[0-9a-f]{3,6});"
            replacement = f"${color_name}: {color_value};"
            style = re.sub(replace_regex, replacement, style)
        CUSTOM_STYLE_SCSS.write_text(style)

        # compile the file with qtsass
        qtsass.compile_filename(CUSTOM_STYLE_SCSS, CUSTOM_STYLE_FILE)
        self.close()

    def _finish_installer_worker(self) -> None:
        """End the spinner, checks if installation was successful."""
        # Informs the user if it is still not found
        if importlib.util.find_spec("qtsass") is None:
            DP_CONTROLLER.say_qtsass_not_successful()
            return
        restart_v1()
