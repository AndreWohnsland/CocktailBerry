from PyQt6.QtWidgets import QMainWindow

from src.database_commander import DatabaseCommander
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.models import EventType
from src.ui_elements import Ui_EventWindow


class EventWindow(QMainWindow, Ui_EventWindow):
    """Creates the event window Widget."""

    def __init__(self) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)
        self.selection_event.activated.connect(self._set_events)
        self.event_types = ["ALL"] + [str(e.value) for e in EventType]
        DP_CONTROLLER.fill_single_combobox(self.selection_event, self.event_types, first_empty=False)
        self._set_events()

        UI_LANGUAGE.adjust_event_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _set_events(self) -> None:
        """Read the current selected log file."""
        event_str: str | None = self.selection_event.currentText()
        # Return if empty selection
        event = None if event_str == "ALL" else [EventType(event_str)]
        self.text_display.setText("\n".join([str(e) for e in DatabaseCommander().get_events(event)]))
