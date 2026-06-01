from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.dialog_handler import DIALOG_HANDLER as DH
from src.display_controller import DP_CONTROLLER
from src.machine.controller import MachineController
from src.models import Cocktail, Ingredient

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


@dataclass
class _MeasureRow:
    """Widgets backing one weighable (ml) hand-add row."""

    ingredient: Ingredient
    container: QWidget
    measure_button: QPushButton
    progress: QProgressBar
    cancel_button: QPushButton


class HandAddMeasureScreen(QMainWindow):
    """Scale-assisted hand-add window (v1).

    Lists weighable (ml) hand adds with a measure button each and non-ml hand adds as
    static instructions. The owning loop calls :meth:`tick` to poll the scale during an
    active measurement (a re-tare runs on each measure click, so rows can be done in any
    order). Sets :attr:`finished` when the user taps Finish, closes the window, or all
    measurable rows are done while there are no text-only rows to confirm.
    """

    def __init__(self, parent: MainScreen, cocktail: Cocktail) -> None:
        super().__init__()
        self.mainscreen = parent
        self.finished = False
        self._mc = MachineController()
        self._active: _MeasureRow | None = None
        self._rows: list[_MeasureRow] = []

        hand_adds = [i for i in cocktail.handadds if i.amount > 0]
        measurable = [i for i in hand_adds if i.unit == "ml"]
        text_only = [i for i in hand_adds if i.unit != "ml"]
        self._text_only_count = len(text_only)

        central = QWidget()
        layout = QVBoxLayout(central)
        title = QLabel(DH.get_translation("hand_add_title"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        for ingredient in measurable:
            row = self._build_measure_row(ingredient)
            self._rows.append(row)
            layout.addWidget(row.container)

        if text_only:
            layout.addWidget(QLabel(DH.get_translation("hand_add_by_hand")))
            for ingredient in text_only:
                layout.addWidget(QLabel(f"{ingredient.name}: {ingredient.amount} {ingredient.unit}"))

        layout.addStretch()
        finish_button = QPushButton(DH.get_translation("hand_add_finish_button"))
        finish_button.clicked.connect(self._finish)
        layout.addWidget(finish_button)

        self.setCentralWidget(central)
        DP_CONTROLLER.initialize_window_object(self)
        # the run loop owns this window's lifetime (it calls close() in its finally), so disable
        # auto-delete-on-close to avoid closing a window whose C++ object was already deleted
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _build_measure_row(self, ingredient: Ingredient) -> _MeasureRow:
        container = QWidget()
        row_layout = QHBoxLayout(container)
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.hide()
        measure_button = QPushButton(DH.get_translation("hand_add_measure"))
        cancel_button = QPushButton(DH.get_translation("hand_add_cancel"))
        cancel_button.hide()
        row_layout.addWidget(QLabel(ingredient.name))
        row_layout.addStretch()
        row_layout.addWidget(QLabel(f"{ingredient.amount} {ingredient.unit}"))
        row_layout.addWidget(progress)
        row_layout.addWidget(measure_button)
        row_layout.addWidget(cancel_button)
        row = _MeasureRow(ingredient, container, measure_button, progress, cancel_button)
        measure_button.clicked.connect(lambda: self._start_measure(row))
        cancel_button.clicked.connect(self._cancel_measure)
        return row

    def tick(self) -> None:
        """Poll the scale once and advance the active measurement (called by the run loop)."""
        row = self._active
        if row is None:
            return
        try:
            grams = self._mc.scale_read_grams()
        except RuntimeError:
            return
        target = row.ingredient.amount
        pct = 0 if target <= 0 else max(0, min(100, int(grams / target * 100)))
        row.progress.setValue(pct)
        if target > 0 and grams >= target:
            self._complete_active()

    def _start_measure(self, row: _MeasureRow) -> None:
        if self._active is not None:
            return
        try:
            self._mc.scale_tare()
        except RuntimeError:
            # scale became unavailable mid-session; keep the row pending instead of aborting prep
            DP_CONTROLLER.standard_box(DH.get_translation("no_scale_available"), close_time=10)
            return
        self._active = row
        row.progress.setValue(0)
        row.progress.show()
        row.cancel_button.show()
        row.measure_button.hide()
        self._set_measure_enabled(enabled=False)

    def _cancel_measure(self) -> None:
        row = self._active
        if row is None:
            return
        self._active = None
        row.progress.hide()
        row.cancel_button.hide()
        row.measure_button.show()
        self._set_measure_enabled(enabled=True)

    def _complete_active(self) -> None:
        row = self._active
        if row is None:
            return
        self._active = None
        self._rows.remove(row)
        row.container.hide()
        row.container.deleteLater()
        self._set_measure_enabled(enabled=True)
        # auto-finish only when everything weighable is done and nothing needs manual confirmation
        if not self._rows and self._text_only_count == 0:
            self._finish()

    def _set_measure_enabled(self, *, enabled: bool) -> None:
        for row in self._rows:
            row.measure_button.setEnabled(enabled)

    def _finish(self) -> None:
        self.finished = True

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        # ensure the owning run loop terminates if the window is closed by any means
        self.finished = True
        if a0 is not None:
            super().closeEvent(a0)
