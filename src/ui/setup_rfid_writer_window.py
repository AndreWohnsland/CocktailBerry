from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLineEdit, QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.machine.rfid import RFIDReader
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements.rfidwriter import Ui_RFIDWriterWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class RFIDWriterWindow(QMainWindow, Ui_RFIDWriterWindow):
    """Class for the Option selection window."""

    def __init__(self, mainscreen: MainScreen) -> None:
        """Initialize the Option selection window."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = mainscreen

        self.button_back.clicked.connect(self._close_window)
        self.button_write.clicked.connect(self._write_rfid)
        self.input_text.clicked.connect(lambda: self._open_keyboard(self.input_text))

        self.keyboard_window: KeyboardWidget | None = None
        self.rfid = RFIDReader()

        UI_LANGUAGE.adjust_rfid_reader_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _write_rfid(self) -> None:
        """Try to write the label to the RFID."""
        text = self.input_text.text()
        if len(text) < 3:
            self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("error"))
            return
        self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("prompt"))
        self.button_write.setDisabled(True)
        self.rfid.write_rfid(text, self._display_success)

    def _close_window(self) -> None:
        self.rfid.cancel_reading()
        self.close()

    def __del__(self) -> None:
        self.rfid.cancel_reading()

    def _display_success(self, _: str) -> None:
        self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("success"))
        self.button_write.setDisabled(False)

    def _open_keyboard(self, le_to_write: QLineEdit, max_char_len: int = 30) -> None:
        """Open up the keyboard connected to the lineedit."""
        self.keyboard_window = KeyboardWidget(self.mainscreen, le_to_write=le_to_write, max_char_len=max_char_len)
