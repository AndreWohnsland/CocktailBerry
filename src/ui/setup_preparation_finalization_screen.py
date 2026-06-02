from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config.config_manager import CONFIG as cfg
from src.dialog_handler import DIALOG_HANDLER as DH
from src.display_controller import DP_CONTROLLER
from src.machine.controller import MachineController
from src.models import Cocktail, HandAddMeasure
from src.ui.creation_utils import FontSize, create_button, create_label, create_spacer, set_strike_through
from src.ui.icons import LARGE_BUTTON_SIZE, IconSetter

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_NAME_LABEL_MAX_WIDTH = 300
# cap the rows block and center it on wide screens (space | items | space), mirroring v2's mx-auto max-w
_ROWS_MAX_WIDTH = 600
# let wrapped completion text grow to its full height instead of being clipped by create_label's 200px default
_MESSAGE_MAX_HEIGHT = 16777215
# uniform action-button / progress-bar height so a row never changes height when the value swaps
_ROW_HEIGHT = 70
# columns: action | name | value, where the value cell swaps amount <-> progress (mirrors v2)
_COL_ACTION = 0
_COL_NAME = 1
_COL_VALUE = 2
_GRID_COLUMNS = 3


def _format_hand_add_amount(amount_ml: int, unit: str) -> str:
    """Render a hand-add amount for display, applying the experimental maker factor/unit to ml.

    Visual only: the measure progress always uses the raw ml amount. Mirrors the rounding used on
    the cocktail selection screen (integer once the value is large enough, else one decimal).
    """
    if unit == "ml":
        value: float = amount_ml * cfg.EXP_MAKER_FACTOR
        display_unit = cfg.EXP_MAKER_UNIT
        threshold = 8
    else:
        value = amount_ml
        display_unit = unit
        threshold = 0
    display_amount = int(round(value, 0)) if value >= threshold else round(value, 1)
    return f"{display_amount} {display_unit}"


@dataclass
class _MeasureRow:
    """The toggleable widgets of one weighable (ml) hand-add row."""

    progress: QProgressBar
    measure_button: QPushButton
    cancel_button: QPushButton
    done_check: QPushButton
    amount_label: QWidget
    name_label: QWidget


@dataclass
class _ManualRow:
    """The widgets of one by-hand (non-measured) hand-add row."""

    check_button: QPushButton
    done_check: QPushButton
    amount_label: QWidget
    name_label: QWidget


class PreparationFinalizationScreen(QMainWindow):
    """Scale-assisted hand-add window.

    Weighable (ml) hand adds get a measure button + progress bar (the run loop calls :meth:`tick`
    to poll the scale; rows resolve in any order); non-ml hand adds get a confirm button. Resolving
    a row keeps it in place: the action becomes a borderless secondary check, the labels are struck
    through, and a measure row's bar fills to 100%. When all rows resolve, they are replaced by a
    completion message that the run loop lingers on before closing. Sets :attr:`finished` on Finish,
    window close, or full resolution.
    """

    def __init__(
        self, parent: MainScreen, cocktail: Cocktail, hand_adds: list[HandAddMeasure], message: str = ""
    ) -> None:
        super().__init__()
        self.mainscreen = parent
        self.finished = False
        # set on auto-finish (all rows resolved): the run loop lingers on the completion message
        self.linger_before_close = False
        # set on a deliberate close (Finish / window close) to skip / interrupt the linger
        self.close_requested = False
        self._mc = MachineController()
        self._icons = IconSetter()
        # the published list is the single source of truth (same as v2); `measurable` is already gated
        self._pending = [h for h in hand_adds if h.measurable]
        self._text_only = [h for h in hand_adds if not h.measurable]
        self._active: HandAddMeasure | None = None
        self._active_progress: QProgressBar | None = None
        self._done: set[int] = set()
        self._rows: dict[int, _MeasureRow] = {}
        self._manual_rows: dict[int, _ManualRow] = {}

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(
            create_label(cocktail.display_name, FontSize.HEADER, bold=True, centered=True, css_class="secondary")
        )
        self._intro_label = create_label(
            DH.get_translation("hand_add_intro"),
            FontSize.MEDIUM,
            centered=True,
            css_class="neutral",
            word_wrap=True,
        )
        layout.addWidget(self._intro_label)
        layout.addItem(create_spacer(20))
        # rows in their own widget so they can be hidden as a unit on completion
        self._rows_widget = QWidget()
        self._rows_widget.setMaximumWidth(_ROWS_MAX_WIDTH)
        self._grid = QGridLayout(self._rows_widget)
        # the value column fills the row, so swapping amount <-> progress inside it never shifts width
        self._grid.setColumnStretch(_COL_VALUE, 1)
        # center the capped-width rows: the high stretch lets them fill up to the cap, then the equal
        # side stretches split the leftover evenly (space | items | space)
        rows_row = QHBoxLayout()
        rows_row.addStretch(1)
        rows_row.addWidget(self._rows_widget, 100)
        rows_row.addStretch(1)
        layout.addLayout(rows_row)
        # completion view shown once resolved: check + (all-done if hand-adds) + optional message
        self._completion_widget = self._build_completion_widget(message)
        self._completion_widget.hide()
        layout.addWidget(self._completion_widget)
        layout.addStretch()
        finish_button = create_button(DH.get_translation("hand_add_finish_button"), font_size=FontSize.LARGE)
        finish_button.clicked.connect(self._finish_now)
        layout.addWidget(finish_button)
        self._build_grid()

        self.setCentralWidget(central)
        DP_CONTROLLER.initialize_window_object(self)
        # the run loop closes this window in its finally; don't auto-delete on close (avoids double-free)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)
        # message-only (no hand-adds) resolves straight to the completion view (0 == 0 done)
        self._check_auto_finish()

    def _build_completion_widget(self, message: str) -> QWidget:
        """Completion view: a check, the all-done line (only if there were hand-adds), then any message."""
        widget = QWidget()
        completion_layout = QVBoxLayout(widget)
        completion_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_icon = self._icons.generate_icon(self._icons.presets.check, self._icons.color.secondary)
        icon_label.setPixmap(check_icon.pixmap(LARGE_BUTTON_SIZE))
        completion_layout.addWidget(icon_label)
        if self._pending or self._text_only:
            message = f"{DH.get_translation('hand_add_all_done')}\n\n{message}"
        if message:
            completion_layout.addWidget(
                create_label(
                    message,
                    FontSize.LARGE,
                    centered=True,
                    word_wrap=True,
                    min_h=300,
                    max_h=_MESSAGE_MAX_HEIGHT,
                )
            )
        completion_layout.addStretch()
        return widget

    def _show_completion(self) -> None:
        """Replace the resolved rows with the completion message."""
        self._intro_label.hide()
        self._rows_widget.hide()
        self._completion_widget.show()

    def _build_grid(self) -> None:
        """Build the grid once from the data model. Rows are resolved in place, never rebuilt."""
        grid_row = 0
        if self._pending:
            grid_row = self._add_section_header(DH.get_translation("hand_add_title"), grid_row)
            for hand_add in self._pending:
                self._rows[id(hand_add)] = self._build_measure_row(hand_add, grid_row)
                grid_row += 1
        if self._text_only:
            grid_row = self._add_section_header(DH.get_translation("hand_add_by_hand"), grid_row)
            for hand_add in self._text_only:
                self._manual_rows[id(hand_add)] = self._build_manual_row(hand_add, grid_row)
                grid_row += 1

    def _add_section_header(self, text: str, grid_row: int) -> int:
        """Add a full-width section header and return the next grid row."""
        header = create_label(text, FontSize.LARGE, bold=True, centered=True, css_class="secondary")
        self._grid.addWidget(header, grid_row, 0, 1, _GRID_COLUMNS)
        return grid_row + 1

    def _name_label(self, hand_add: HandAddMeasure) -> QWidget:
        return create_label(f"  {hand_add.name} ", FontSize.LARGE, bold=True, max_w=_NAME_LABEL_MAX_WIDTH)

    def _amount_label(self, hand_add: HandAddMeasure) -> QWidget:
        return create_label(
            text=f"  {_format_hand_add_amount(hand_add.amount, hand_add.unit)}",
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

    def _flat_icon_button(self, icon_name: str, color: str) -> QPushButton:
        """Build a borderless icon-only button (glyph tinted with its own color, no fill/border)."""
        button = create_button(
            "", font_size=FontSize.LARGE, min_w=90, max_w=120, min_h=_ROW_HEIGHT, css_class="no-border"
        )
        self._icons.set_icon(button, self._icons.generate_icon(icon_name, color), no_text=True, size=LARGE_BUTTON_SIZE)
        return button

    def _build_measure_row(self, hand_add: HandAddMeasure, grid_row: int) -> _MeasureRow:
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
        # done marker; inert (no slot connected)
        done_check = self._flat_icon_button(self._icons.presets.check, self._icons.color.secondary)
        done_check.hide()
        progress.hide()
        amount_label = self._amount_label(hand_add)
        name_label = self._name_label(hand_add)

        align_right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        # measure / cancel / done-check share the action cell; amount + progress share the value cell
        self._grid.addWidget(measure_button, grid_row, _COL_ACTION)
        self._grid.addWidget(cancel_button, grid_row, _COL_ACTION)
        self._grid.addWidget(done_check, grid_row, _COL_ACTION)
        self._grid.addWidget(name_label, grid_row, _COL_NAME)
        self._grid.addWidget(amount_label, grid_row, _COL_VALUE, align_right)
        self._grid.addWidget(progress, grid_row, _COL_VALUE)

        measure_button.clicked.connect(lambda: self._start_measure(hand_add))
        cancel_button.clicked.connect(self._cancel_measure)
        return _MeasureRow(
            progress=progress,
            measure_button=measure_button,
            cancel_button=cancel_button,
            done_check=done_check,
            amount_label=amount_label,
            name_label=name_label,
        )

    def _build_manual_row(self, hand_add: HandAddMeasure, grid_row: int) -> _ManualRow:
        # empty-circle "to-do" affordance (mirrors v2's FaRegCircle)
        check_button = self._flat_icon_button(self._icons.presets.circle, self._icons.color.primary)
        done_check = self._flat_icon_button(self._icons.presets.check, self._icons.color.secondary)
        done_check.hide()
        amount_label = self._amount_label(hand_add)
        name_label = self._name_label(hand_add)
        check_button.clicked.connect(lambda: self._confirm_manual(hand_add))
        align_right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        self._grid.addWidget(check_button, grid_row, _COL_ACTION)
        self._grid.addWidget(done_check, grid_row, _COL_ACTION)
        self._grid.addWidget(name_label, grid_row, _COL_NAME)
        self._grid.addWidget(amount_label, grid_row, _COL_VALUE, align_right)
        return _ManualRow(
            check_button=check_button,
            done_check=done_check,
            amount_label=amount_label,
            name_label=name_label,
        )

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

    def _start_measure(self, hand_add: HandAddMeasure) -> None:
        if self._active is not None:
            return
        try:
            self._mc.scale_tare()
        except RuntimeError:
            # scale became unavailable mid-session; keep the row pending instead of aborting prep
            DP_CONTROLLER.standard_box(DH.get_translation("no_scale_available"), close_time=10)
            return
        row = self._rows[id(hand_add)]
        self._active = hand_add
        self._active_progress = row.progress
        row.progress.setValue(0)
        # swap the value cell to the progress bar
        row.amount_label.hide()
        row.progress.show()
        row.cancel_button.show()
        row.measure_button.hide()
        # lock the other rows' actions while one measurement runs (single scale, one at a time)
        self._set_actions_enabled(enabled=False)

    def _cancel_measure(self) -> None:
        if self._active is None:
            return
        row = self._rows[id(self._active)]
        row.progress.setValue(0)
        # swap the value cell back to the amount
        row.progress.hide()
        row.amount_label.show()
        row.cancel_button.hide()
        row.measure_button.show()
        self._active = None
        self._active_progress = None
        self._set_actions_enabled(enabled=True)

    def _complete_active(self) -> None:
        if self._active is None:
            return
        hand_add = self._active
        self._active = None
        self._active_progress = None
        self._set_actions_enabled(enabled=True)
        self._resolve_row(hand_add)
        self._check_auto_finish()

    def _confirm_manual(self, hand_add: HandAddMeasure) -> None:
        self._resolve_row(hand_add)
        self._check_auto_finish()

    def _resolve_row(self, hand_add: HandAddMeasure) -> None:
        """Mark a row done in place: swap to the borderless secondary check and strike out the labels."""
        self._done.add(id(hand_add))
        measure_row = self._rows.get(id(hand_add))
        if measure_row is not None:
            measure_row.measure_button.hide()
            measure_row.cancel_button.hide()
            # done shows the struck amount again, not the bar
            measure_row.progress.hide()
            measure_row.amount_label.show()
            measure_row.done_check.show()
            self._mark_done(measure_row.amount_label, measure_row.name_label)
        manual_row = self._manual_rows.get(id(hand_add))
        if manual_row is not None:
            manual_row.check_button.hide()
            manual_row.done_check.show()
            self._mark_done(manual_row.amount_label, manual_row.name_label)

    def _mark_done(self, *labels: QWidget) -> None:
        """Dim (neutral) and strike through resolved-row labels."""
        for label in labels:
            # restyle to neutral first, then set the strike-out font so the repolish can't drop it
            label.setProperty("cssClass", "neutral")
            style = label.style()
            if style is not None:
                style.unpolish(label)
                style.polish(label)
            set_strike_through(label, True)

    def _check_auto_finish(self) -> None:
        # all rows resolved → show the completion message and let the run loop linger before closing
        if len(self._done) == len(self._pending) + len(self._text_only):
            self._show_completion()
            self.linger_before_close = True
            self._finish()

    def _set_actions_enabled(self, *, enabled: bool) -> None:
        # leave resolved rows alone; their interactive button is already hidden
        for ingredient_id, row in self._rows.items():
            if ingredient_id not in self._done:
                row.measure_button.setEnabled(enabled)
        for ingredient_id, manual_row in self._manual_rows.items():
            if ingredient_id not in self._done:
                manual_row.check_button.setEnabled(enabled)

    def _finish(self) -> None:
        self.finished = True

    def _finish_now(self) -> None:
        # user tapped Finish: close immediately (skip / interrupt the completion linger)
        self.close_requested = True
        self.finished = True

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        # ensure the owning run loop terminates if the window is closed by any means
        self.close_requested = True
        self.finished = True
        if a0 is not None:
            super().closeEvent(a0)
