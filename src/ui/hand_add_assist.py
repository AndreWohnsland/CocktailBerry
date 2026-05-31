from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.machine.controller import MachineController
from src.models import HandAddAssistItem

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class HandAddMeasureDialog(QDialog):
    """Simple progress dialog for measuring a single hand-add with the scale."""

    def __init__(self, parent: MainScreen, item: HandAddAssistItem) -> None:
        super().__init__(parent)
        self.item = item
        self.mc = MachineController()
        self.setObjectName("handAddMeasureDialog")
        DP_CONTROLLER.initialize_window_object(self)
        DP_CONTROLLER.set_display_settings(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(24)

        header = QLabel(UI_LANGUAGE.get_translation("measure_title", "handadds_window", ingredient=item.name))
        header.setWordWrap(True)
        header.setStyleSheet("font-size: 28px;")
        layout.addWidget(header)

        target = item.target_weight_grams or 0.0
        self.target_label = QLabel(
            UI_LANGUAGE.get_translation("measure_target", "handadds_window", amount=f"{target:.1f}")
        )
        self.current_label = QLabel(
            UI_LANGUAGE.get_translation("measure_current", "handadds_window", amount="0.0")
        )
        layout.addWidget(self.target_label)
        layout.addWidget(self.current_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setMinimumHeight(40)
        layout.addWidget(self.progress)

        self.back_button = QPushButton(UI_LANGUAGE.get_translation("back", "generics"))
        self.back_button.clicked.connect(self.reject)
        layout.addWidget(self.back_button)

        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._poll_scale)

    def exec(self) -> int:
        try:
            self.mc.scale_tare()
        except RuntimeError as error:
            self.current_label.setText(str(error))
            return super().exec()
        self.timer.start()
        self.showFullScreen()
        return super().exec()

    def _poll_scale(self) -> None:
        target = self.item.target_weight_grams or 0.0
        if target <= 0:
            self._stop_timer()
            self.reject()
            return
        try:
            current_weight = max(0.0, self.mc.scale_read_grams())
        except RuntimeError as error:
            self.current_label.setText(str(error))
            self._stop_timer()
            return
        self.current_label.setText(
            UI_LANGUAGE.get_translation("measure_current", "handadds_window", amount=f"{current_weight:.1f}")
        )
        progress = min(100, round(current_weight / target * 100))
        self.progress.setValue(progress)
        if current_weight >= target:
            self._stop_timer()
            self.accept()

    def reject(self) -> None:
        self._stop_timer()
        super().reject()

    def accept(self) -> None:
        self._stop_timer()
        super().accept()

    def _stop_timer(self) -> None:
        if self.timer.isActive():
            self.timer.stop()


class HandAddAssistDialog(QDialog):
    """Simple full-screen list of pending hand-add steps."""

    def __init__(self, parent: MainScreen, items: list[HandAddAssistItem], intro_message: str = "") -> None:
        super().__init__(parent)
        self.items = items
        self.completed_ids: set[str] = set()
        self.setObjectName("handAddAssistDialog")
        DP_CONTROLLER.initialize_window_object(self)
        DP_CONTROLLER.set_display_settings(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(18)

        header = QLabel(UI_LANGUAGE.get_translation("title", "handadds_window"))
        header.setStyleSheet("font-size: 30px;")
        layout.addWidget(header)

        if intro_message:
            info_label = QLabel(intro_message)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setSpacing(12)
        self.scroll_area.setWidget(self.scroll_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.finish_button = QPushButton(UI_LANGUAGE.get_translation("finish", "handadds_window"))
        self.finish_button.clicked.connect(self.accept)
        layout.addWidget(self.finish_button)

        self._render_items()

    def exec(self) -> int:
        self.showFullScreen()
        return super().exec()

    def _render_items(self) -> None:
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        for item in self.items:
            row = QFrame()
            row_layout = QHBoxLayout(row)

            label = QLabel(
                UI_LANGUAGE.get_translation(
                    "instruction",
                    "handadds_window",
                    ingredient=item.name,
                    amount=item.display_amount,
                    unit=item.display_unit,
                )
            )
            row_layout.addWidget(label, stretch=1)

            if item.item_id in self.completed_ids:
                done_label = QLabel(UI_LANGUAGE.get_translation("done", "generics"))
                row_layout.addWidget(done_label)
            else:
                button_name = "measure" if item.measurable else "mark_done"
                button = QPushButton(UI_LANGUAGE.get_translation(button_name, "handadds_window"))
                button.clicked.connect(lambda _checked=False, current_item=item: self._handle_item(current_item))
                row_layout.addWidget(button)

            self.scroll_layout.addWidget(row)

        self.scroll_layout.addStretch()

    def _handle_item(self, item: HandAddAssistItem) -> None:
        if item.measurable:
            dialog = HandAddMeasureDialog(self.parent(), item)  # type: ignore[arg-type]
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
        self.completed_ids.add(item.item_id)
        self._render_items()
        if len(self.completed_ids) == len(self.items):
            self.accept()


def run_hand_add_assist_dialog(w: MainScreen, items: list[HandAddAssistItem], intro_message: str = "") -> None:
    """Run the Qt hand-add helper if there are pending items."""
    if not items:
        return
    dialog = HandAddAssistDialog(w, items, intro_message=intro_message)
    dialog.exec()
