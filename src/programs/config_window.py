from __future__ import annotations

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.display_controller import DP_CONTROLLER as DPC
from src.error_handler import logerror
from src.ui.create_config_window import ConfigWindow


@logerror
def run_config_window(message: str | None = None, disable_back: bool = True) -> None:
    """Execute the config window as standalone."""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    app = QApplication(sys.argv)
    window = ConfigWindow(None)
    if disable_back:
        window.button_back.setDisabled(True)
    if message:
        DPC.standard_box(message)
    sys.exit(app.exec_())
