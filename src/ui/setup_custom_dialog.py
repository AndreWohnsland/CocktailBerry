from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.customdialog import Ui_CustomDialog


class CustomDialog(QMainWindow, Ui_CustomDialog):
    """Class for the Team selection Screen."""

    def __init__(
        self,
        message: str,
        title: str = "Information",
        use_ok: bool = False,
        close_callback: Callable | None = None,
        close_time: int | None = None,
    ) -> None:
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.informationLabel.setText(message)
        self.setWindowTitle(title)
        self.closeButton.clicked.connect(self.close_clicked)
        self.close_callback = close_callback
        self.close_time = close_time
        self._timer: QTimer | None = None

        UI_LANGUAGE.adjust_custom_dialog(self, use_ok)

    def close_clicked(self) -> None:
        if self.close_callback is not None:
            self.close_callback()
        self.close()

    def _start_close_timer(self) -> None:
        if self.close_time is not None:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self.close)  # type: ignore[arg-type]
            self._timer.start(int(self.close_time * 1000))

    def show_non_blocking(self) -> None:
        self._start_close_timer()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def exec(self) -> bool:
        self._start_close_timer()
        loop = QEventLoop()
        self.destroyed.connect(loop.quit)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        loop.exec()
        return True

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if self._timer and self._timer.isActive():
            self._timer.stop()
        super().closeEvent(event)
