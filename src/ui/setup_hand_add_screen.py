from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QGridLayout, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QWidget

from src.dialog_handler import DIALOG_HANDLER as DH
from src.display_controller import DP_CONTROLLER
from src.machine.controller import MachineController
from src.models import Cocktail, Ingredient
from src.ui.creation_utils import FontSize, create_button, create_label
from src.ui.icons import LARGE_BUTTON_SIZE, IconSetter

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

# cap the ingredient name so it does not eat half the row; the progress column gets the rest
_NAME_LABEL_MAX_WIDTH = 200
# shared height for the action buttons and the progress bar, so a row looks uniform
_ROW_HEIGHT = 70
# grid columns
_COL_NAME = 0
_COL_PROGRESS = 1
_COL_AMOUNT = 2
_COL_ACTION = 3


@dataclass
class _MeasureRow:
    """The toggleable widgets of one weighable (ml) hand-add row."""

    progress: QProgressBar
    measure_button: QPushButton
    cancel_button: QPushButton


class HandAddMeasureScreen(QMainWindow):
    """Scale-assisted hand-add window (v1).

    Lists weighable (ml) hand adds with a measure button each and non-ml hand adds as
    static instructions. The owning loop calls :meth:`tick` to poll the scale during an
    active measurement (a re-tare runs on each measure click, so rows can be done in any
    order). When a row reaches its target it is dropped and the grid is rebuilt. Sets
    :attr:`finished` when the user taps Finish, closes the window, or all measurable rows
    are done while there are no text-only rows to confirm.
    """

    def __init__(self, parent: MainScreen, cocktail: Cocktail) -> None:
        super().__init__()
        self.mainscreen = parent
        self.finished = False
        self._mc = MachineController()
        self._icons = IconSetter()
        # data model: rebuilt into the grid whenever a row is completed
        hand_adds = [i for i in cocktail.handadds if i.amount > 0]
        self._pending = [i for i in hand_adds if i.unit == "ml"]
        self._text_only = [i for i in hand_adds if i.unit != "ml"]
        self._active: Ingredient | None = None
        self._active_progress: QProgressBar | None = None
        self._rows: dict[int, _MeasureRow] = {}

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(
            create_label(
                DH.get_translation("hand_add_title"), FontSize.HEADER, bold=True, centered=True, css_class="secondary"
            )
        )
        self._grid = QGridLayout()
        # the progress column expands, the name/amount/action columns stay compact
        self._grid.setColumnStretch(_COL_PROGRESS, 1)
        layout.addLayout(self._grid)
        layout.addStretch()
        finish_button = create_button(DH.get_translation("hand_add_finish_button"), font_size=FontSize.LARGE)
        finish_button.clicked.connect(self._finish)
        layout.addWidget(finish_button)
        self._rebuild_grid()

        self.setCentralWidget(central)
        DP_CONTROLLER.initialize_window_object(self)
        # the run loop owns this window's lifetime (it calls close() in its finally), so disable
        # auto-delete-on-close to avoid closing a window whose C++ object was already deleted
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _rebuild_grid(self) -> None:
        """Rebuild the grid from the current data model (clean recompute, no stale rows)."""
        DP_CONTROLLER.delete_items_of_layout(self._grid)
        self._rows = {}
        grid_row = 0
        for ingredient in self._pending:
            self._rows[id(ingredient)] = self._build_measure_row(ingredient, grid_row)
            grid_row += 1
        if self._text_only:
            self._grid.addWidget(
                create_label(DH.get_translation("hand_add_by_hand"), FontSize.MEDIUM, bold=True), grid_row, 0, 1, 4
            )
            grid_row += 1
            for ingredient in self._text_only:
                self._grid.addWidget(self._name_label(ingredient), grid_row, _COL_NAME)
                self._grid.addWidget(self._amount_label(ingredient), grid_row, _COL_AMOUNT)
                grid_row += 1

    def _name_label(self, ingredient: Ingredient) -> QWidget:
        return create_label(f"  {ingredient.name} ", FontSize.LARGE, bold=True, max_w=_NAME_LABEL_MAX_WIDTH)

    def _amount_label(self, ingredient: Ingredient) -> QWidget:
        return create_label(
            text=f"{ingredient.amount} {ingredient.unit}  ",
            font_size=FontSize.LARGE,
            bold=True,
            css_class="secondary",
            centered=True,
        )

    def _icon_button(self, icon_name: str, css_class: str) -> QPushButton:
        """Build a filled, icon-only action button (icon tinted to contrast the filled background)."""
        button = create_button(
            "", font_size=FontSize.LARGE, min_w=90, max_w=120, min_h=_ROW_HEIGHT, css_class=css_class
        )
        icon = self._icons.generate_icon(icon_name, self._icons.color.background)
        self._icons.set_icon(button, icon, no_text=True, size=LARGE_BUTTON_SIZE)
        return button

    def _build_measure_row(self, ingredient: Ingredient, grid_row: int) -> _MeasureRow:
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setMinimumHeight(_ROW_HEIGHT)  # match the action buttons' height
        progress.hide()
        measure_button = self._icon_button(self._icons.presets.measure, "btn-inverted")
        cancel_button = self._icon_button(self._icons.presets.close, "btn-inverted destructive")
        cancel_button.hide()

        self._grid.addWidget(self._name_label(ingredient), grid_row, _COL_NAME)
        self._grid.addWidget(self._amount_label(ingredient), grid_row, _COL_AMOUNT)
        self._grid.addWidget(progress, grid_row, _COL_PROGRESS)
        # measure and cancel share the action cell; only one is visible at a time
        self._grid.addWidget(measure_button, grid_row, _COL_ACTION)
        self._grid.addWidget(cancel_button, grid_row, _COL_ACTION)

        measure_button.clicked.connect(lambda: self._start_measure(ingredient))
        cancel_button.clicked.connect(self._cancel_measure)
        return _MeasureRow(progress=progress, measure_button=measure_button, cancel_button=cancel_button)

    def tick(self) -> None:
        """Poll the scale once and advance the active measurement (called by the run loop)."""
        if self._active is None or self._active_progress is None:
            return
        try:
            grams = self._mc.scale_read_grams()
        except RuntimeError:
            return
        target = self._active.amount
        pct = 0 if target <= 0 else max(0, min(100, int(grams / target * 100)))
        self._active_progress.setValue(pct)
        if target > 0 and grams >= target:
            self._complete_active()

    def _start_measure(self, ingredient: Ingredient) -> None:
        if self._active is not None:
            return
        try:
            self._mc.scale_tare()
        except RuntimeError:
            # scale became unavailable mid-session; keep the row pending instead of aborting prep
            DP_CONTROLLER.standard_box(DH.get_translation("no_scale_available"), close_time=10)
            return
        row = self._rows[id(ingredient)]
        self._active = ingredient
        self._active_progress = row.progress
        row.progress.setValue(0)
        row.progress.show()
        row.cancel_button.show()
        row.measure_button.hide()
        self._set_measure_enabled(enabled=False)

    def _cancel_measure(self) -> None:
        if self._active is None:
            return
        row = self._rows[id(self._active)]
        row.progress.hide()
        row.cancel_button.hide()
        row.measure_button.show()
        self._active = None
        self._active_progress = None
        self._set_measure_enabled(enabled=True)

    def _complete_active(self) -> None:
        if self._active is None:
            return
        self._pending.remove(self._active)
        self._active = None
        self._active_progress = None
        # rebuild so the finished row is gone and the remaining rows are laid out cleanly
        self._rebuild_grid()
        # auto-finish only when everything weighable is done and nothing needs manual confirmation
        if not self._pending and not self._text_only:
            self._finish()

    def _set_measure_enabled(self, *, enabled: bool) -> None:
        for row in self._rows.values():
            row.measure_button.setEnabled(enabled)

    def _finish(self) -> None:
        self.finished = True

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        # ensure the owning run loop terminates if the window is closed by any means
        self.finished = True
        if a0 is not None:
            super().closeEvent(a0)
