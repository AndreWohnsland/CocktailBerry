from typing import Callable, Optional
from PyQt5.QtWidgets import QWidget, QSpacerItem, QSizePolicy, QPushButton, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize, QObject, QThread, Qt

from src.ui.icons import ICONS

SMALL_FONT = 14
MEDIUM_FONT = 16
LARGE_FONT = 18
HEADER_FONT = 22


class FontSize:
    SMALL = SMALL_FONT
    MEDIUM = MEDIUM_FONT
    LARGE = LARGE_FONT


def adjust_font(element: QWidget, font_size: int, bold: bool = False):
    """Adjust the font to given size and optional bold"""
    font = QFont()
    font.setPointSize(font_size)
    font.setBold(bold)
    weight = 75 if bold else 50
    font.setWeight(weight)
    element.setFont(font)


def create_spacer(height: int, width: int = 20, expand: bool = False):
    """Creates a spacer of given height and optional width"""
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
    css_class: Optional[str] = None
):
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
    css_class: Optional[str] = None
):
    """Creates a label with given text and properties"""
    label = QLabel(text)
    adjust_font(label, font_size, bold)
    if centered:
        label.setAlignment(Qt.AlignCenter)  # type: ignore
    if css_class is not None:
        label.setProperty("cssClass", css_class)
    return label


def setup_worker_thread(worker: QObject, parent: QWidget, after_finish: Callable):
    """Moves worker the thread and set necessary things (spinner, eg) up
    Worker needs done = pyqtSignal() and emit that at the end of run function
    """
    ICONS.start_spinner(parent)
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
    _thread.finished.connect(ICONS.stop_spinner)  # type: ignore[attr-defined]

    return _thread


def generate_bottle_management(row: int):
    """Generates a row for bottle management"""
    return row
