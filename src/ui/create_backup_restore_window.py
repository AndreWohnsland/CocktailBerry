import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.migration.backup import FILE_SELECTION_MAPPER, NEEDED_BACKUP_FILES
from src.ui.creation_utils import HEADER_FONT, LARGE_FONT, adjust_font, create_button, create_label, create_spacer
from src.utils import restart_program

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class BackupRestoreWindow(QMainWindow):
    def __init__(self, parent: MainScreen, backup_path: Path) -> None:
        super().__init__()
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        self.backup_path = backup_path
        self.config_objects: dict[str, QCheckBox] = {}
        self._init_ui()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _init_ui(self) -> None:
        # This is not shown (full screen) and only for dev reasons. need no translation
        self.setWindowTitle("Restore Backup")
        # init the central widget with its container layout
        self.central_widget = QWidget(self)
        self.layout_container = QVBoxLayout(self.central_widget)
        # adds a scroll area with props, and its contents
        self.scroll_area = QScrollArea(self.central_widget)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # type: ignore
        self.scroll_area.setFrameShadow(QFrame.Plain)  # type: ignore
        self.scroll_area_widget_contents = QWidget()
        # this is the layout inside the scroll area
        self.vbox = QVBoxLayout(self.scroll_area_widget_contents)
        # self.vbox.setAlignment(Qt.AlignCenter)  # type: ignore

        # header with the expander
        self.header = create_label(
            UI_LANGUAGE.get_translation("header", "backup_window"),
            font_size=HEADER_FONT,
            centered=True,
            css_class="secondary",
            bold=True,
        )
        self.vbox.addWidget(self.header)
        self.vbox.addItem(create_spacer(20, 100, True))

        # adds the checkboxes for the backup files
        self._generate_checkboxes()
        # adds a spacer
        self.vbox.addItem(create_spacer(20, 100, True))

        # adds the back button
        self.button_back = create_button(UI_LANGUAGE.get_translation("back"), max_h=100)
        self.button_back.clicked.connect(self.close)  # type: ignore[attr-defined]
        # adds the save button
        self.button_save = create_button(UI_LANGUAGE.get_translation("apply"), max_h=100, css_class="btn-inverted")
        self.button_save.clicked.connect(self._upload_backup)  # type: ignore[attr-defined]
        # places them side by side in a container
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.button_back)
        self.hbox.addWidget(self.button_save)
        self.vbox.addLayout(self.hbox)

        # Sets widget of scroll area, adds to container, sets main widget
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.layout_container.addWidget(self.scroll_area)
        self.setCentralWidget(self.central_widget)

    def _upload_backup(self) -> None:
        """Prompt the user for a folder path to load the backup from.

        Loads the config, custom database and version from the location.
        """
        to_backup, description = self._get_needed_backup_paths_and_description()
        description_string = ", ".join(description)
        if not DP_CONTROLLER.ask_backup_overwrite(description_string):
            return
        for _file in to_backup + NEEDED_BACKUP_FILES:
            # needs to differentiate between files and folders
            # this will also not throw an error if the file does not exist
            if _file.is_file():
                shutil.copy(self.backup_path / _file.name, _file)
            if _file.is_dir():
                shutil.copytree(self.backup_path / _file.name, _file, dirs_exist_ok=True)
        restart_program(is_v1=True)

    def _generate_checkboxes(self) -> None:
        """Generate the checkboxes for the backup files."""
        for backup_type, file_paths in FILE_SELECTION_MAPPER.items():
            # if not all needed files exist in the backup, skip
            # This should not happen, but if the user tempers with the backup, it might
            skip = False
            for _file in file_paths:
                backup_file = self.backup_path / _file.name
                if not backup_file.exists():
                    skip = True
                    break
            if skip:
                continue
            translation = UI_LANGUAGE.get_translation(backup_type, "backup_window")
            checkbox = QCheckBox(translation)
            checkbox.setChecked(True)
            checkbox.setProperty("cssClass", "big-checkbox")
            adjust_font(checkbox, LARGE_FONT + 2)
            self.config_objects[backup_type] = checkbox
            # use box the center the checkbox, since you cant just do it with the checkbox by center
            container = QHBoxLayout()
            container.addItem(QSpacerItem(100, 40, QSizePolicy.Expanding, QSizePolicy.Fixed))  # type: ignore
            container.addWidget(checkbox)
            container.addItem(QSpacerItem(100, 40, QSizePolicy.Expanding, QSizePolicy.Fixed))  # type: ignore
            self.vbox.addLayout(container)

    def _get_needed_backup_paths_and_description(self) -> tuple[list[Path], list[str]]:
        """Return the file paths based on user selection."""
        selected_files: list[Path] = []
        description: list[str] = []
        for backup_type, checkbox in self.config_objects.items():
            if checkbox.isChecked():
                selected_files.extend(FILE_SELECTION_MAPPER[backup_type])
                description.append(UI_LANGUAGE.get_translation(backup_type, "backup_window"))
        return selected_files, description
