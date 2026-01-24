from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMainWindow

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements import Ui_NewsWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

# TODO: add translation keys once implemented
_NEWS_KEYS: list[str] = []


class NewsWindow(QMainWindow, Ui_NewsWindow):
    """Creates the news window Widget."""

    def __init__(self, mainscreen: "MainScreen") -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        self.mainscreen = mainscreen
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)

        UI_LANGUAGE.adjust_news_window(self)
        self._render_news()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _render_news(self) -> None:
        """Render not removed/acknowledged news items."""
        # TODO: get news items data from database
        # (method to get by key + method will get and enter missing with default value)

    def _acknowledge_news(self, news_key: str) -> None:
        """Acknowledge a news item so it won't be shown again."""
        # TODO: update database and remove element from self.data_container
        # NOTE: need to recursively delete and remove each item in the element of the news
