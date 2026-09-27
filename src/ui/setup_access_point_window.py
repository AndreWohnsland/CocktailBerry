from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLineEdit, QMainWindow

from src.connection import access_point
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.logger_handler import LoggerHandler
from src.ui.icons import IconSetter
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements import Ui_AccessPointWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("access_point_setup")


class AccessPointWindow(QMainWindow, Ui_AccessPointWindow):
    """Window to enable, disable and configure the access point."""

    def __init__(self, mainscreen: MainScreen) -> None:
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = mainscreen
        self.keyboard_window: KeyboardWidget | None = None

        self.button_back.clicked.connect(self.close)  # pyright: ignore[reportArgumentType]
        self.button_apply.clicked.connect(self._apply_process)
        self.input_ssid.clicked.connect(lambda: self._open_keyboard(self.input_ssid, access_point.SSID_LENGTH[1]))
        self.input_ssid.textChanged.connect(self._check_valid_inputs)
        self.input_password.clicked.connect(
            lambda: self._open_keyboard(self.input_password, access_point.PASSWORD_LENGTH[1])
        )
        self.input_password.textChanged.connect(self._check_valid_inputs)

        UI_LANGUAGE.adjust_access_point_window(self)
        self._show_status(access_point.read_ap())
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _show_status(self, status: access_point.ApStatus) -> None:
        self.input_ssid.setText(status.ssid)
        self.input_password.setText(status.password)
        self.checkbox_enabled.setChecked(status.enabled)
        if not status.enabled:
            self.label_qr.setPixmap(QPixmap())
            self.label_qr.setText(UI_LANGUAGE.get_translation("qr_hint", "access_point"))
            return
        pixmap = QPixmap()
        pixmap.loadFromData(access_point.ap_qr_png(status.ssid, status.password))
        self.label_qr.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))

    def _check_valid_inputs(self) -> None:
        ssid_ok = access_point.SSID_LENGTH[0] <= len(self.input_ssid.text()) <= access_point.SSID_LENGTH[1]
        pw_ok = access_point.PASSWORD_LENGTH[0] <= len(self.input_password.text()) <= access_point.PASSWORD_LENGTH[1]
        self.button_apply.setDisabled(not (ssid_ok and pw_ok))

    def _open_keyboard(self, le_to_write: QLineEdit, max_char_len: int) -> None:
        self.keyboard_window = KeyboardWidget(self.mainscreen, le_to_write=le_to_write, max_char_len=max_char_len)

    def _apply_process(self) -> None:
        """Apply the settings, uses a spinner during progress."""
        icons = IconSetter()
        icons.set_wait_icon(self.button_apply)
        QApplication.processEvents()
        self._apply()
        icons.remove_icon(self.button_apply)
        QApplication.processEvents()

    def _apply(self) -> None:
        try:
            access_point.apply_ap(self.checkbox_enabled.isChecked(), self.input_ssid.text(), self.input_password.text())
        except (OSError, subprocess.SubprocessError) as e:
            _logger.error(f"Access point setup failed: {e}")
            _logger.log_exception(e)
            DP_CONTROLLER.say_ap_setup_failed()
            return
        self._show_status(access_point.read_ap())
        DP_CONTROLLER.say_ap_applied(access_point.AP_ADDRESS)
