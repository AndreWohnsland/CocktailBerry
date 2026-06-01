from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QWidget

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import DIALOG_HANDLER as DH
from src.display_controller import DP_CONTROLLER
from src.machine.controller import MachineController
from src.models import Cocktail, Ingredient
from src.ui.creation_utils import FontSize, create_button, create_label, create_spacer
from src.ui.icons import LARGE_BUTTON_SIZE, IconSetter

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

# cap the ingredient name so it does not eat half the row; the progress column gets the rest
_NAME_LABEL_MAX_WIDTH = 200
# shared height for the action buttons and the progress bar, so a row looks uniform
_ROW_HEIGHT = 70
# grid columns (mirrors the v2 layout: action | amount | name | progress)
_COL_ACTION = 0
_COL_AMOUNT = 1
_COL_NAME = 2
_COL_PROGRESS = 3
_GRID_COLUMNS = 4


@dataclass
class _MeasureRow:
    """The toggleable widgets of one weighable (ml) hand-add row."""

    progress: QProgressBar
    measure_button: QPushButton
    cancel_button: QPushButton


class HandAddMeasureScreen(QMainWindow):
    """Scale-assisted hand-add window (v1).

    One aligned grid holds both sections (mirroring v2): weighable (ml) hand adds get a measure
    button + progress bar (the owning loop calls :meth:`tick` to poll the scale during an active
    measurement; a re-tare runs on each measure click, so rows can be done in any order), and
    non-ml hand adds get a check button to confirm they were added by hand. Resolving a row drops
    it and rebuilds the grid. Sets :attr:`finished` when the user taps Finish, closes the window,
    or every row is resolved.
    """

    def __init__(self, parent: MainScreen, cocktail: Cocktail) -> None:
        super().__init__()
        self.mainscreen = parent
        self.finished = False
        self._mc = MachineController()
        self._icons = IconSetter()
        # data model: rebuilt into the grid whenever a row is resolved
        # ml items get a measure button only when the scale feature is on and a scale is present;
        # otherwise (and for non-ml items) they are confirmed by hand via a check button
        scale_measuring = bool(cfg.MAKER_SCALE_FOR_HAND_ADDS and self._mc.has_scale)
        hand_adds = [i for i in cocktail.handadds if i.amount > 0]
        self._pending = [i for i in hand_adds if i.unit == "ml" and scale_measuring]
        self._text_only = [i for i in hand_adds if not (i.unit == "ml" and scale_measuring)]
        # stable for the cocktail's lifetime (does not change as measure rows complete)
        self._has_measurable = bool(self._pending)
        self._active: Ingredient | None = None
        self._active_progress: QProgressBar | None = None
        self._rows: dict[int, _MeasureRow] = {}
        self._manual_buttons: list[QPushButton] = []

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(
            create_label(cocktail.display_name, FontSize.HEADER, bold=True, centered=True, css_class="secondary")
        )
        layout.addWidget(
            create_label(
                DH.get_translation("hand_add_intro"),
                FontSize.MEDIUM,
                centered=True,
                css_class="neutral",
                word_wrap=True,
            )
        )
        # breathing room between the instruction and the rows below
        layout.addItem(create_spacer(20))
        self._grid = QGridLayout()
        if self._has_measurable:
            # the progress column fills the row; rows stay left-aligned with the bar reaching the edge
            self._grid.setColumnStretch(_COL_PROGRESS, 1)
            layout.addLayout(self._grid)
        else:
            # no progress column to align to: center the content-sized grid (matches v2's manual-only)
            centered_row = QHBoxLayout()
            centered_row.addStretch()
            centered_row.addLayout(self._grid)
            centered_row.addStretch()
            layout.addLayout(centered_row)
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
        self._manual_buttons = []
        grid_row = 0
        if self._pending:
            grid_row = self._add_section_header(DH.get_translation("hand_add_title"), grid_row)
            for ingredient in self._pending:
                self._rows[id(ingredient)] = self._build_measure_row(ingredient, grid_row)
                grid_row += 1
        if self._text_only:
            grid_row = self._add_section_header(DH.get_translation("hand_add_by_hand"), grid_row)
            for ingredient in self._text_only:
                self._build_manual_row(ingredient, grid_row)
                grid_row += 1

    def _add_section_header(self, text: str, grid_row: int) -> int:
        """Add a full-width section header and return the next grid row."""
        header = create_label(text, FontSize.LARGE, bold=True, centered=True, css_class="secondary")
        self._grid.addWidget(header, grid_row, 0, 1, _GRID_COLUMNS)
        return grid_row + 1

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
        self._icons.set_icon(
            button,
            self._icons.generate_icon(icon_name, self._icons.color.background),
            no_text=True,
            size=LARGE_BUTTON_SIZE,
        )
        return button

    def _build_measure_row(self, ingredient: Ingredient, grid_row: int) -> _MeasureRow:
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setMinimumSize(QSize(0, _ROW_HEIGHT))
        progress.setMaximumSize(QSize(16777215, 200))
        font = QFont()
        font.setPointSize(FontSize.LARGE)
        font.setBold(True)
        progress.setFont(font)
        measure_button = self._icon_button(self._icons.presets.measure, "btn-inverted")
        cancel_button = self._icon_button(self._icons.presets.close, "btn-inverted destructive")
        cancel_button.hide()

        self._grid.addWidget(measure_button, grid_row, _COL_ACTION)
        # measure and cancel share the action cell; only one is visible at a time
        self._grid.addWidget(cancel_button, grid_row, _COL_ACTION)
        self._grid.addWidget(self._amount_label(ingredient), grid_row, _COL_AMOUNT)
        self._grid.addWidget(self._name_label(ingredient), grid_row, _COL_NAME)
        self._grid.addWidget(progress, grid_row, _COL_PROGRESS)

        measure_button.clicked.connect(lambda: self._start_measure(ingredient))
        cancel_button.clicked.connect(self._cancel_measure)
        return _MeasureRow(progress=progress, measure_button=measure_button, cancel_button=cancel_button)

    def _build_manual_row(self, ingredient: Ingredient, grid_row: int) -> None:
        # same columns as a measure row, minus the progress bar (its column stays empty)
        check_button = self._icon_button(self._icons.presets.check, "btn-inverted")
        check_button.clicked.connect(lambda: self._confirm_manual(ingredient))
        self._grid.addWidget(check_button, grid_row, _COL_ACTION)
        self._grid.addWidget(self._amount_label(ingredient), grid_row, _COL_AMOUNT)
        self._grid.addWidget(self._name_label(ingredient), grid_row, _COL_NAME)
        self._manual_buttons.append(check_button)

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
        row.cancel_button.show()
        row.measure_button.hide()
        # lock the other rows' actions while one measurement runs (avoids a rebuild mid-measure)
        self._set_actions_enabled(enabled=False)

    def _cancel_measure(self) -> None:
        if self._active is None:
            return
        row = self._rows[id(self._active)]
        row.progress.setValue(0)
        row.cancel_button.hide()
        row.measure_button.show()
        self._active = None
        self._active_progress = None
        self._set_actions_enabled(enabled=True)

    def _complete_active(self) -> None:
        if self._active is None:
            return
        self._pending.remove(self._active)
        self._active = None
        self._active_progress = None
        # rebuild so the finished row is gone and the remaining rows are laid out cleanly
        self._rebuild_grid()
        self._check_auto_finish()

    def _confirm_manual(self, ingredient: Ingredient) -> None:
        self._text_only.remove(ingredient)
        self._rebuild_grid()
        self._check_auto_finish()

    def _check_auto_finish(self) -> None:
        # auto-finish once every row (measured + manually confirmed) is resolved
        if not self._pending and not self._text_only:
            self._finish()

    def _set_actions_enabled(self, *, enabled: bool) -> None:
        for row in self._rows.values():
            row.measure_button.setEnabled(enabled)
        for button in self._manual_buttons:
            button.setEnabled(enabled)

    def _finish(self) -> None:
        self.finished = True

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        # ensure the owning run loop terminates if the window is closed by any means
        self.finished = True
        if a0 is not None:
            super().closeEvent(a0)
