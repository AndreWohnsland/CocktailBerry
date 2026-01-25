from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMainWindow, QSizePolicy, QVBoxLayout, QWidget

from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER, UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.shared import NEWS_KEYS
from src.ui.creation_utils import FontSize, create_button, create_label
from src.ui_elements import Ui_NewsWindow

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class NewsWindow(QMainWindow, Ui_NewsWindow):
    """Creates the news window Widget."""

    def __init__(self, mainscreen: "MainScreen") -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        self.mainscreen = mainscreen
        self.no_news_text = UI_LANGUAGE.get_translation("no_news", "news_window")
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)

        UI_LANGUAGE.adjust_news_window(self)
        self._render_news()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _render_news(self) -> None:
        """Render not removed/acknowledged news items."""
        DBC = DatabaseCommander()
        unacknowledged_keys = DBC.get_unacknowledged_news_keys(NEWS_KEYS)

        if not unacknowledged_keys:
            no_news_label = create_label(self.no_news_text, FontSize.MEDIUM, centered=True, word_wrap=True)
            self.data_container.addWidget(no_news_label)
            return

        for news_key in unacknowledged_keys:
            news_widget = self._create_news_widget(news_key)
            self.data_container.addWidget(news_widget)

    def _create_news_widget(self, news_key: str) -> QWidget:
        """Create a widget for a single news item."""
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        news_label = create_label(
            DIALOG_HANDLER.get_translation(news_key),  # type: ignore[arg-type]
            FontSize.MEDIUM,
            centered=True,
            word_wrap=True,
            max_h=500,
        )
        layout.addWidget(news_label)

        acknowledge_btn = create_button(
            UI_LANGUAGE.get_translation("acknowledge", "news_window"),
            max_h=80,
            css_class="btn-inverted",
        )
        acknowledge_btn.clicked.connect(lambda _, key=news_key, w=widget: self._acknowledge_news(key, w))
        layout.addWidget(acknowledge_btn)

        widget.setLayout(layout)
        return widget

    def _acknowledge_news(self, news_key: str, widget: QWidget) -> None:
        """Acknowledge a news item so it won't be shown again."""
        DBC = DatabaseCommander()
        DBC.acknowledge_news(news_key)

        self.data_container.removeWidget(widget)
        widget.deleteLater()

        if self.data_container.count() == 0:
            no_news_label = create_label(
                self.no_news_text,
                FontSize.MEDIUM,
                centered=True,
                word_wrap=True,
            )
            self.data_container.addWidget(no_news_label)
