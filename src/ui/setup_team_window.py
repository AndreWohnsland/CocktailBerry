from PyQt5.QtWidgets import QDialog

from src.ui_elements.teamselection import Ui_Teamselection
from src.config_manager import CONFIG as cfg, shared
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.machine.rfid import RFIDReader


class TeamScreen(QDialog, Ui_Teamselection):
    """ Class for the Team selection Screen. """

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.PBteamone.clicked.connect(lambda: self.set_team(cfg.TEAM_BUTTON_NAMES[0]))
        self.PBteamone.setText(cfg.TEAM_BUTTON_NAMES[0])
        self.PBteamtwo.clicked.connect(lambda: self.set_team(cfg.TEAM_BUTTON_NAMES[1]))
        self.PBteamtwo.setText(cfg.TEAM_BUTTON_NAMES[1])
        self.mainscreen = parent
        UI_LANGUAGE.adjust_team_window(self)
        DP_CONTROLLER.set_display_settings(self)
        self.__set_icon_text_breaks()
        self._rfid_reader = None
        # reset the team name, since this needs to be read over rfid
        shared.team_member_name = None
        self.person_label.setText("")
        if cfg.RFID_READER != "No":
            self._rfid_reader = RFIDReader()
            self._rfid_reader.read_rfid(self._write_rfid_value)

    def _write_rfid_value(self, text: str, _id: str):
        shared.team_member_name = text
        self.person_label.setText(text)

    def set_team(self, team: str):
        shared.selected_team = team
        if self._rfid_reader is not None:
            self._rfid_reader.cancel_reading()
        self.close()

    def __del__(self):
        if self._rfid_reader is not None:
            self._rfid_reader.cancel_reading()

    def __set_icon_text_breaks(self):
        """Adds new lines if necessary to team button labels"""
        # ~ 12 upper chars / 400 px
        width = self.PBteamone.frameGeometry().width()
        self.PBteamone.setText(self.__split_team_names(cfg.TEAM_BUTTON_NAMES[0], width))
        self.PBteamtwo.setText(self.__split_team_names(cfg.TEAM_BUTTON_NAMES[1], width))

    def __split_team_names(self, name: str, width: int):
        """Pseudo line wrap, since its not available for button"""
        singles = name.split(" ")
        label = singles[0]
        cur_len = len(label)
        for sing in singles[1::]:
            added_len = len(sing)
            if width / (cur_len + added_len + 1) <= 25:
                label += f"\n{sing}"
                cur_len = added_len
            else:
                cur_len += added_len
                label += f" {sing}"
        return label
