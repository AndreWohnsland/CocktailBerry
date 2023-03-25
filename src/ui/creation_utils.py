from typing import Optional
from PyQt5.QtWidgets import QWidget, QSpacerItem, QSizePolicy, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize

SMALL_FONT = 14
MEDIUM_FONT = 16
LARGE_FONT = 18


def adjust_font(element: QWidget, font_size: int, bold: bool = False):
    """Adjust the font to given size and optional bold"""
    font = QFont()
    font.setPointSize(font_size)
    font.setBold(bold)
    weight = 75 if bold else 50
    font.setWeight(weight)
    element.setFont(font)


def create_spacer(height: int, width: int = 20):
    """Creates a spacer of given height and optional width"""
    return QSpacerItem(width, height, QSizePolicy.Minimum, QSizePolicy.Fixed)  # type: ignore


def create_button(label: str, parent: Optional[QWidget] = None):
    btn = QPushButton(label, parent)
    btn.setMaximumSize(QSize(16777215, 200))
    btn.setMinimumSize(QSize(0, 70))
    adjust_font(btn, LARGE_FONT, True)
    return btn
