from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

from src.machine.rfid import RFIDReader
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements.rfidwriter import Ui_RFIDWriterWindow


class RFIDWriterWindow(QMainWindow, Ui_RFIDWriterWindow):
    """ Class for the Option selection window. """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        self.move(0, 0)

        self.button_back.clicked.connect(self.close)
        self.button_write.clicked.connect(self._write_rfid)

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
        self.rfid.write_rfid(text, self._display_success)

    def _display_success(self, _: str):
        self.label_information.setText(UI_LANGUAGE.get_rfid_information_display("success"))

    def __del__(self):
        self.rfid.cancel_reading()
