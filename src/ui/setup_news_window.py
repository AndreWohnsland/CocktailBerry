from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from src.database_commander import DatabaseCommander
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui_elements import Ui_NewsWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

# List of all available news translation keys
_NEWS_KEYS: list[str] = [
    "news_v2_available",
]


class NewsWindow(QMainWindow, Ui_NewsWindow):
    """Creates the news window Widget."""

    def __init__(self, mainscreen: "MainScreen") -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        self.mainscreen = mainscreen
        self.db_commander = DatabaseCommander()
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)

        UI_LANGUAGE.adjust_news_window(self)
        self._render_news()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _render_news(self) -> None:
        """Render not removed/acknowledged news items."""
        # Get unacknowledged news from database
        unacknowledged_keys = self.db_commander.get_unacknowledged_news_keys(_NEWS_KEYS)
        
        if not unacknowledged_keys:
            # Show placeholder when there are no news
            no_news_label = QLabel(UI_LANGUAGE.get_translation("news_window.no_news"))
            no_news_label.setWordWrap(True)
            no_news_label.setProperty("cssClass", "text-lg")
            self.data_container.addWidget(no_news_label)
            return
        
        # Render each news item
        for news_key in unacknowledged_keys:
            news_widget = self._create_news_widget(news_key)
            self.data_container.addWidget(news_widget)

    def _create_news_widget(self, news_key: str) -> QWidget:
        """Create a widget for a single news item."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # News content label
        news_text = UI_LANGUAGE.get_translation(f"news_window.{news_key}")
        news_label = QLabel(news_text)
        news_label.setWordWrap(True)
        news_label.setProperty("cssClass", "text-base")
        layout.addWidget(news_label)
        
        # Acknowledge button
        acknowledge_btn = QPushButton(UI_LANGUAGE.get_translation("news_window.acknowledge"))
        acknowledge_btn.setProperty("cssClass", "btn-primary")
        acknowledge_btn.clicked.connect(lambda: self._acknowledge_news(news_key, widget))
        layout.addWidget(acknowledge_btn)
        
        widget.setLayout(layout)
        widget.setProperty("cssClass", "card")
        return widget

    def _acknowledge_news(self, news_key: str, widget: QWidget) -> None:
        """Acknowledge a news item so it won't be shown again."""
        # Update database
        self.db_commander.acknowledge_news(news_key)
        
        # Remove widget from layout
        self.data_container.removeWidget(widget)
        widget.deleteLater()
        
        # If no more news, show placeholder
        if self.data_container.count() == 0:
            no_news_label = QLabel(UI_LANGUAGE.get_translation("news_window.no_news"))
            no_news_label.setWordWrap(True)
            no_news_label.setProperty("cssClass", "text-lg")
            self.data_container.addWidget(no_news_label)
