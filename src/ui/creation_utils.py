from typing import Callable, Optional

from PyQt5.QtCore import QObject, QSize, Qt, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGridLayout, QLabel, QProgressBar, QPushButton, QSizePolicy, QSpacerItem, QWidget

from src.ui.icons import IconSetter

SMALL_FONT = 14
MEDIUM_FONT = 16
LARGE_FONT = 18
HEADER_FONT = 22


class FontSize:
    SMALL = SMALL_FONT
    MEDIUM = MEDIUM_FONT
    LARGE = LARGE_FONT


class RowCounter:
    def __init__(self, value: int = 0) -> None:
        self.value = value


def adjust_font(element: QWidget, font_size: int, bold: bool = False) -> None:
    """Adjust the font to given size and optional bold."""
    font = QFont()
    font.setPointSize(font_size)
    font.setBold(bold)
    weight = 75 if bold else 50
    font.setWeight(weight)
    element.setFont(font)


def set_underline(element: QWidget, underline: bool) -> None:
    """Set the strike through property of the font."""
    font = element.font()
    font.setUnderline(underline)
    element.setFont(font)


def set_strike_through(element: QWidget, strike_through: bool) -> None:
    """Set the strike through property of the font."""
    font = element.font()
    font.setStrikeOut(strike_through)
    element.setFont(font)


def create_spacer(height: int, width: int = 20, expand: bool = False) -> QSpacerItem:
    """Create a spacer of given height and optional width."""
    policy = QSizePolicy.Expanding if expand else QSizePolicy.Fixed  # type: ignore
    return QSpacerItem(width, height, QSizePolicy.Minimum, policy)  # type: ignore


def create_button(
    label: str,
    parent: Optional[QWidget] = None,
    font_size: int = LARGE_FONT,
    max_w: int = 16777215,
    max_h: int = 200,
    min_w: int = 0,
    min_h: int = 70,
    bold: bool = True,
    css_class: Optional[str] = None,
) -> QPushButton:
    btn = QPushButton(label, parent)
    btn.setMaximumSize(QSize(max_w, max_h))
    btn.setMinimumSize(QSize(min_w, min_h))
    adjust_font(btn, font_size, bold)
    if css_class is not None:
        btn.setProperty("cssClass", css_class)
    return btn


def create_label(
    text: str,
    font_size: int,
    bold: bool = False,
    centered: bool = False,
    max_w: int = 16777215,
    max_h: int = 200,
    min_w: int = 0,
    min_h: int = 20,
    css_class: Optional[str] = None,
    word_wrap: bool = False,
) -> QLabel:
    """Create a label with given text and properties."""
    label = QLabel(text)
    label.setMaximumSize(QSize(max_w, max_h))
    label.setMinimumSize(QSize(min_w, min_h))
    adjust_font(label, font_size, bold)
    if centered:
        label.setAlignment(Qt.AlignCenter)  # type: ignore
    if css_class is not None:
        label.setProperty("cssClass", css_class)
    if word_wrap:
        label.setWordWrap(True)
    return label


def setup_worker_thread(worker: QObject, parent: QWidget, after_finish: Callable) -> QThread:
    """Move worker the thread and set necessary things (spinner, eg) up.

    Worker needs done = pyqtSignal() and emit that at the end of run function.
    """
    icons = IconSetter()
    icons.start_spinner(parent)
    # Create a  thread object. move worker to thread
    _thread = QThread()  # pylint: disable=attribute-defined-outside-init
    worker.moveToThread(_thread)

    # Connect signals and slots
    _thread.started.connect(worker.run)  # type: ignore
    worker.done.connect(_thread.quit)  # type: ignore
    worker.done.connect(worker.deleteLater)  # type: ignore
    _thread.finished.connect(_thread.deleteLater)  # type: ignore[attr-defined]

    # Start the thread, connect to the finish function
    _thread.start()
    _thread.finished.connect(after_finish)  # type: ignore[attr-defined]
    _thread.finished.connect(icons.stop_spinner)  # type: ignore[attr-defined]

    return _thread


def add_grid_spacer(grid: QGridLayout, row_counter: RowCounter) -> None:
    """Add a spacer to the grid layout and increment row."""
    spacer_label = create_label("", 12)
    spacer_label.setMaximumSize(QSize(16777215, 30))
    grid.addWidget(spacer_label, row_counter.value, 0, 1, 1)
    row_counter.value += 1


def add_grid_text(grid: QGridLayout, row_counter: RowCounter, text: str, font_size: int = MEDIUM_FONT) -> None:
    """Add a text to the grid layout and increment row."""
    text_label = create_label(text, font_size, False, True)
    grid.addWidget(text_label, row_counter.value, 0, 1, 3)
    row_counter.value += 1


def add_grid_header(grid: QGridLayout, row_counter: RowCounter, text: str) -> None:
    """Add a header to the grid layout and increment row by 2."""
    header_label = create_label(text, 20, True, True, css_class="header-underline", min_h=40, max_h=50)
    grid.addWidget(header_label, row_counter.value, 0, 1, 3)
    row_counter.value += 2


def generate_grid_bar_chart(
    parent: QWidget,
    grid: QGridLayout,
    row_counter: RowCounter,
    names: list,
    values: list,
    quantifier: str = "x",
) -> None:
    """Generate one bar in the grid for each name/value and increment row."""
    if not values:
        return
    max_value = max(values)
    for name, value in zip(names, values):
        grid.addWidget(create_label(f"{name} ", 20, False, True), row_counter.value, 0, 1, 1)
        grid.addWidget(
            create_label(f" {value}{quantifier} ", 20, True, True, css_class="secondary"), row_counter.value, 1, 1, 1
        )
        displayed_bar = QProgressBar(parent)
        displayed_bar.setTextVisible(False)
        displayed_bar.setProperty("cssClass", "no-bg")
        displayed_bar.setValue(int(100 * value / max_value) if max_value else 0)
        grid.addWidget(displayed_bar, row_counter.value, 2, 1, 1)
        row_counter.value += 1


def generate_bottle_management(row: int) -> int:
    """Generate a row for bottle management."""
    return row
