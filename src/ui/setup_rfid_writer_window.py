from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from src.machine.rfid import RFIDReader
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements.rfidwriter import Ui_RFIDWriterWindow

if TYPE_CHECKING:
    from src.ui_elements import Ui_MainWindow


class RFIDWriterWindow(QMainWindow, Ui_RFIDWriterWindow):
    """ Class for the Option selection window. """

    def __init__(self, mainscreen: Ui_MainWindow):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        self.move(0, 0)
        self.mainscreen = mainscreen

        self.button_back.clicked.connect(self.close)
        self.button_write.clicked.connect(self._write_rfid)
        self.input_text.clicked.connect(lambda: self._open_keyboard(self.input_text))

        self.keyboard_window: Optional[KeyboardWidget] = None
        self.rfid = RFIDReader()

        UI_LANGUAGE.adjust_rfid_reader_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _write_rfid(self):
        """Try to write the label to the RFID"""
        text = self.input_text.text()
        if len(text) < 3:
            self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("error"))
            return
        self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("prompt"))
        self.button_write.setDisabled(True)
        self.rfid.write_rfid(text, self._display_success)

    def __del__(self):
        self.rfid.cancel_reading()

    def _display_success(self, _: str):
        self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("success"))
        self.button_write.setDisabled(False)

    def _open_keyboard(self, le_to_write, max_char_len=30):
        """ Opens up the keyboard connected to the lineedit """
        self.keyboard_window = KeyboardWidget(self.mainscreen, le_to_write=le_to_write, max_char_len=max_char_len)
