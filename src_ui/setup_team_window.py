from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog

from ui_elements.teamselection import Ui_Teamselection
from config.config_manager import ConfigManager, shared
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE


class TeamScreen(QDialog, Ui_Teamselection, ConfigManager):
    """ Class for the Team selection Screen. """

    def __init__(self, parent=None):
        super().__init__()
        ConfigManager.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.PBteamone.clicked.connect(lambda: set_team(self.TEAM_BUTTON_NAMES[0]))
        self.PBteamone.setText(self.TEAM_BUTTON_NAMES[0])
        self.PBteamtwo.clicked.connect(lambda: set_team(self.TEAM_BUTTON_NAMES[1]))
        self.PBteamtwo.setText(self.TEAM_BUTTON_NAMES[1])
        self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        self.move(0, 0)
        UI_LANGUAGE.adjust_team_window(self)
        DP_CONTROLLER.set_dev_settings(self)

        def set_team(team: str):
            shared.selected_team = team
            self.close()
