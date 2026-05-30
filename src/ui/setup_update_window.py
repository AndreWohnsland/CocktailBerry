from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEventLoop
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.update_window import Ui_UpdateWindow

if TYPE_CHECKING:
    from src.updater import VersionInfo


class UpdateWindow(QMainWindow, Ui_UpdateWindow):
    """Version selection + release-notes window for software updates (v1).

    Shows a dropdown of available versions. When the selection changes the release
    notes and (if applicable) a major-update warning are updated immediately.
    Clicking the yes-button confirms the update; the no-button cancels it.
    """

    def __init__(
        self,
        versions: list[VersionInfo],
        major_marker: str,
    ) -> None:
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self._versions = versions
        self._label_to_tag: dict[str, str] = {}
        self._result: str | None = None
        self._loop: QEventLoop | None = None

        for v in versions:
            label = f"{v.version}  \u26a0 {major_marker}" if v.is_major else v.version
            self._label_to_tag[label] = v.version
            self.selection_version.addItem(label)
        # default to the last (highest) entry
        self.selection_version.setCurrentIndex(len(versions) - 1)

        self.yes_button.clicked.connect(self._yes_clicked)
        self.no_button.clicked.connect(self._no_clicked)
        self.selection_version.currentIndexChanged.connect(self._refresh)

        UI_LANGUAGE.adjust_update_window(self)
        self._refresh()

    def _refresh(self) -> None:
        """Show/hide warning label and update release notes to match the current selection."""
        tag = self._label_to_tag.get(self.selection_version.currentText())
        info = next((v for v in self._versions if v.version == tag), None)
        if info is None:
            return
        self.label_release_information.setText(info.release_notes)
        self.label_warning.setVisible(info.is_major)

    def _yes_clicked(self) -> None:
        self._result = self._label_to_tag.get(self.selection_version.currentText())
        self._finish()

    def _no_clicked(self) -> None:
        self._result = None
        self._finish()

    def _finish(self) -> None:
        if self._loop is not None:
            self._loop.quit()
        self.close()

    def exec(self) -> str | None:
        """Show fullscreen, block until user confirms or cancels. Returns the selected tag or None."""
        self._loop = QEventLoop()
        self.destroyed.connect(self._loop.quit)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        self._loop.exec()
        return self._result

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._loop is not None and self._loop.isRunning():
            self._result = None
            self._loop.quit()
        super().closeEvent(a0)
