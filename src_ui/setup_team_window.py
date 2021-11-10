from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog

from ui_elements.teamselection import Ui_Teamselection
from config.config_manager import ConfigManager, shared


class TeamScreen(QDialog, Ui_Teamselection, ConfigManager):
    """ Class for the Team selection Screen. """

    def __init__(self, parent=None):
        super(TeamScreen, self).__init__(parent)
        ConfigManager.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.PBteamone.clicked.connect(lambda: set_team(self.TEAM_BUTTON_NAMES[0]))
        self.PBteamone.setText(self.TEAM_BUTTON_NAMES[0])
        self.PBteamtwo.clicked.connect(lambda: set_team(self.TEAM_BUTTON_NAMES[1]))
        self.PBteamtwo.setText(self.TEAM_BUTTON_NAMES[1])
        self.setWindowIcon(QIcon(parent.icon_path))
        self.mainscreen = parent
        if not self.mainscreen.UI_DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        self.move(0, 0)

        def set_team(team: str):
            shared.selected_team = team
            self.close()
