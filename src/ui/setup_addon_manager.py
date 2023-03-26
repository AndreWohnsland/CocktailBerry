from dataclasses import dataclass
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView
# from PyQt5.QtCore import Qt

from src.ui_elements import Ui_AddonManager
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.programs.addons import ADDONS


@dataclass
class _AddonData:
    name: str = "Not Set"
    description: str = "Not Set"
    url: str = "Not Set"


class AddonManager(QMainWindow, Ui_AddonManager):
    """ Creates A window to display addon GUI for the user"""

    def __init__(self, parent=None):
        """ Initializes the object """
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        # connects all the buttons
        self.button_back.clicked.connect(self.close)
        self.button_apply.clicked.connect(self._apply_changes)
        self._installed_addons = list(ADDONS.addons.keys())
        self.available_addons = self._get_addons_available()
        self._fill_addon_list()

        UI_LANGUAGE.adjust_addon_manager(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _fill_addon_list(self):
        self.table_addons.setRowCount(len(self.available_addons))
        self.table_addons.setColumnCount(2)
        for i, addon in enumerate(self.available_addons):
            name_cell = QTableWidgetItem(addon.name)
            self.table_addons.setItem(i, 0, name_cell)
            description_cell = QTableWidgetItem(addon.description)
            self.table_addons.setItem(i, 1, description_cell)

        headers = ["name", "description"]
        self.table_addons.setHorizontalHeaderLabels(headers)
        self.table_addons.horizontalHeader().setStretchLastSection(True)
        self.table_addons.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore
        self.table_addons.resizeRowsToContents()

    def _get_addons_available(self):
        return [
            _AddonData(**{
                "name": "Testaddon",
                "description": "bla blaaaa blaaaaaa",
                "url": "https.//github.com/addon.py",
            }),
            _AddonData(**{
                "name": "Testaddon1",
                "description": "bla blaaaa blaaaaaa adfdf",
                "url": "https.//github.com/addon1.py",
            }),
            _AddonData(**{
                "name": "Testaddon2",
                "description": "bla blaaaa blaaaaaa stqwagdfgh sdfd fsdfsdf sdf sdf s sfdsdf fs fsdf sdfsdf sdfa  sudg 9s sufh9sd fh9sdfs9 hf9sfhsd9fhud9fhs9  h9dfis9r<Z=SDFGUS",
                "url": "https.//github.com/addon2.py",
            })
        ]

    def _apply_changes(self):
        pass
