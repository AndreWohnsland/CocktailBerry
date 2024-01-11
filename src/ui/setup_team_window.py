from itertools import cycle
from PyQt5.QtWidgets import QDialog

from src.ui_elements.teamselection import Ui_Teamselection
from src.config_manager import CONFIG as cfg, shared
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.machine.rfid import RFIDReader
from src.ui.creation_utils import create_button


class TeamScreen(QDialog, Ui_Teamselection):
    """ Class for the Team selection Screen. """

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # iterate over all team names and add a button for each
        team_colors = cycle(["btn-teamone", "btn-teamtwo"])
        for team_name in cfg.TEAM_BUTTON_NAMES:
            team_button = create_button(team_name, font_size=40, max_h=300, min_h=100, css_class=next(team_colors))
            team_button.clicked.connect(lambda _, t=team_name: self.set_team(t))
            self.button_container.addWidget(team_button)
            setattr(self, f"button_{team_name}", team_button)
        self.mainscreen = parent
        UI_LANGUAGE.adjust_team_window(self)
        DP_CONTROLLER.set_display_settings(self)
        # self.__set_icon_text_breaks()
        self._rfid_reader = None
        # reset the team name, since this needs to be read over rfid
        shared.team_member_name = None
        self.person_label.setText("")
        if cfg.RFID_READER != "No":
            self._rfid_reader = RFIDReader()
            self._rfid_reader.read_rfid(self._write_rfid_value)
        else:
            # we do not need the person label, so remove it
            self.person_label.deleteLater()

    def _write_rfid_value(self, text: str, _id: str):
        shared.team_member_name = text
        self.person_label.setText(text)

    def set_team(self, team: str):
        print(f"Team {team} selected")
        shared.selected_team = team
        if self._rfid_reader is not None:
            self._rfid_reader.cancel_reading()
        # self.close()

    def __del__(self):
        if self._rfid_reader is not None:
            self._rfid_reader.cancel_reading()
