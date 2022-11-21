from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog

from src.ui_elements.teamselection import Ui_Teamselection
from src.config_manager import CONFIG as cfg, shared
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE


class TeamScreen(QDialog, Ui_Teamselection):
    """ Class for the Team selection Screen. """

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        self.PBteamone.clicked.connect(lambda: self.set_team(cfg.TEAM_BUTTON_NAMES[0]))
        self.PBteamone.setText(cfg.TEAM_BUTTON_NAMES[0])
        self.PBteamtwo.clicked.connect(lambda: self.set_team(cfg.TEAM_BUTTON_NAMES[1]))
        self.PBteamtwo.setText(cfg.TEAM_BUTTON_NAMES[1])
        if parent is not None:
            self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        self.move(0, 0)
        UI_LANGUAGE.adjust_team_window(self)
        DP_CONTROLLER.set_display_settings(self)
        self.__set_icon_text_breaks()

    def set_team(self, team: str):
        shared.selected_team = team
        self.close()

    def __set_icon_text_breaks(self):
        """Adds new lines if neccecary to team button labels"""
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
