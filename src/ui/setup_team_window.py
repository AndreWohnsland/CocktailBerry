from itertools import cycle
from typing import Callable
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from src.ui_elements.teamselection import Ui_Teamselection
from src.config_manager import CONFIG as cfg, shared
from src.display_controller import DP_CONTROLLER
from src.dialog_handler import UI_LANGUAGE
from src.machine.rfid import RFIDReader
from src.ui.creation_utils import create_button
from src.service_handler import SERVICE_HANDLER


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
        # spin up worker to get data and not block action
        self._worker = self._Worker(self._get_leaderboard_data)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        # Connect signals and slots
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

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
        self.close()

    def __del__(self):
        if self._rfid_reader is not None:
            self._rfid_reader.cancel_reading()

    def _get_leaderboard_data(self):
        """Get leaderboard data.
        Change the button afterwards with the number as prefix in brackets
        """
        data = SERVICE_HANDLER.get_team_data()
        for name, number in data.items():
            try:
                button = getattr(self, f"button_{name}")
                button.setText(f"{name} ({number}x)")
            except AttributeError:
                pass

    class _Worker(QObject):
        """Worker to install qtsass on a thread"""
        done = pyqtSignal()

        def __init__(self, func: Callable, parent=None):
            super().__init__(parent)
            self.func = func

        def run(self):
            self.func()
            self.done.emit()
