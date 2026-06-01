from __future__ import annotations

from dataclasses import dataclass, field
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
_NAME_LABEL_MAX_WIDTH = 320
# qtawesome name for the new measure (scale) icon
_MEASURE_ICON = "mdi6.scale-balance"
# grid columns
_COL_NAME = 0
_COL_AMOUNT = 1
_COL_PROGRESS = 2
_COL_ACTION = 3


@dataclass
class _MeasureRow:
    """Widgets backing one weighable (ml) hand-add row in the grid."""

    ingredient: Ingredient
    progress: QProgressBar
    measure_button: QPushButton
    cancel_button: QPushButton
    cells: list[QWidget] = field(default_factory=list)


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
        self._icons = IconSetter()
        self._active: _MeasureRow | None = None
        self._rows: list[_MeasureRow] = []

        hand_adds = [i for i in cocktail.handadds if i.amount > 0]
        measurable = [i for i in hand_adds if i.unit == "ml"]
        text_only = [i for i in hand_adds if i.unit != "ml"]
        self._text_only_count = len(text_only)

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
        grid_row = 0
        for ingredient in measurable:
            self._build_measure_row(ingredient, grid_row)
            grid_row += 1
        if text_only:
            self._grid.addWidget(
                create_label(DH.get_translation("hand_add_by_hand"), FontSize.MEDIUM, bold=True), grid_row, 0, 1, 4
            )
            grid_row += 1
            for ingredient in text_only:
                self._grid.addWidget(self._name_label(ingredient), grid_row, _COL_NAME)
                self._grid.addWidget(self._amount_label(ingredient), grid_row, _COL_AMOUNT)
                grid_row += 1
        layout.addLayout(self._grid)
        layout.addStretch()

        finish_button = create_button(DH.get_translation("hand_add_finish_button"), font_size=FontSize.LARGE)
        finish_button.clicked.connect(self._finish)
        layout.addWidget(finish_button)

        self.setCentralWidget(central)
        DP_CONTROLLER.initialize_window_object(self)
        # the run loop owns this window's lifetime (it calls close() in its finally), so disable
        # auto-delete-on-close to avoid closing a window whose C++ object was already deleted
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _name_label(self, ingredient: Ingredient) -> QWidget:
        return create_label(ingredient.name, FontSize.LARGE, max_w=_NAME_LABEL_MAX_WIDTH, word_wrap=True)

    def _amount_label(self, ingredient: Ingredient) -> QWidget:
        return create_label(f"{ingredient.amount} {ingredient.unit}", FontSize.LARGE, css_class="secondary")

    def _icon_button(self, icon_name: str, css_class: str) -> QPushButton:
        """Build a filled, icon-only action button (icon tinted to contrast the filled background)."""
        button = create_button("", font_size=FontSize.LARGE, min_w=90, max_w=120, css_class=css_class)
        icon = self._icons.generate_icon(icon_name, self._icons.color.background)
        self._icons.set_icon(button, icon, no_text=True, size=LARGE_BUTTON_SIZE)
        return button

    def _build_measure_row(self, ingredient: Ingredient, grid_row: int) -> None:
        name = self._name_label(ingredient)
        amount = self._amount_label(ingredient)
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.hide()
        measure_button = self._icon_button(_MEASURE_ICON, "btn-inverted")
        cancel_button = self._icon_button(self._icons.presets.close, "btn-inverted destructive")
        cancel_button.hide()

        self._grid.addWidget(name, grid_row, _COL_NAME)
        self._grid.addWidget(amount, grid_row, _COL_AMOUNT)
        self._grid.addWidget(progress, grid_row, _COL_PROGRESS)
        # measure and cancel share the action cell; only one is visible at a time
        self._grid.addWidget(measure_button, grid_row, _COL_ACTION)
        self._grid.addWidget(cancel_button, grid_row, _COL_ACTION)

        row = _MeasureRow(
            ingredient=ingredient,
            progress=progress,
            measure_button=measure_button,
            cancel_button=cancel_button,
            cells=[name, amount, progress, measure_button, cancel_button],
        )
        measure_button.clicked.connect(lambda: self._start_measure(row))
        cancel_button.clicked.connect(self._cancel_measure)
        self._rows.append(row)

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
        # drop the row's widgets; the emptied grid row collapses to zero height (no gap)
        for cell in row.cells:
            self._grid.removeWidget(cell)
            cell.deleteLater()
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
