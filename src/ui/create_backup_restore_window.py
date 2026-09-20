from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
from src.migration.backup import FILE_SELECTION_MAPPER, files_for_groups, restore_backup
from src.ui.creation_utils import HEADER_FONT, LARGE_FONT, adjust_font, create_button, create_label, create_spacer
from src.utils import restart_v1

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class BackupRestoreWindow(QMainWindow):
    def __init__(self, parent: "MainScreen", backup_path: Path) -> None:
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
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area_widget_contents = QWidget()
        # this is the layout inside the scroll area
        self.vbox = QVBoxLayout(self.scroll_area_widget_contents)
        # self.vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.button_back.clicked.connect(self.close)
        # adds the save button
        self.button_save = create_button(UI_LANGUAGE.get_translation("apply"), max_h=100, css_class="btn-inverted")
        self.button_save.clicked.connect(self._upload_backup)
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
        groups, description = self._get_selected_groups_and_description()
        if not DP_CONTROLLER.ask_backup_overwrite(", ".join(description)):
            return
        restore_backup(self.backup_path, files_for_groups(groups))
        restart_v1()

    def _generate_checkboxes(self) -> None:
        """Generate the checkboxes for the backup files."""
        for backup_type, file_paths in FILE_SELECTION_MAPPER.items():
            # only offer a type the backup can actually deliver, a v2-made backup has no styles
            if not all((self.backup_path / _file.name).exists() for _file in file_paths):
                continue
            translation = UI_LANGUAGE.get_translation(backup_type, "backup_window")
            checkbox = QCheckBox(translation)
            checkbox.setChecked(True)
            checkbox.setProperty("cssClass", "big-checkbox")
            adjust_font(checkbox, LARGE_FONT + 2)
            self.config_objects[backup_type] = checkbox
            # use box the center the checkbox, since you cant just do it with the checkbox by center
            container = QHBoxLayout()
            container.addItem(QSpacerItem(100, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
            container.addWidget(checkbox)
            container.addItem(QSpacerItem(100, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
            self.vbox.addLayout(container)

    def _get_selected_groups_and_description(self) -> tuple[list[str], list[str]]:
        """Return the selected backup types and their translated names."""
        selected_groups: list[str] = []
        description: list[str] = []
        for backup_type, checkbox in self.config_objects.items():
            if checkbox.isChecked():
                selected_groups.append(backup_type)
                description.append(UI_LANGUAGE.get_translation(backup_type, "backup_window"))
        return selected_groups, description
