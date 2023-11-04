from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QGridLayout, QScrollArea, QFrame
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy

from src.models import Cocktail
from src.ui_elements.clickable_label import ClickableLabel
from src.image_utils import find_cocktail_image
from src.config_manager import CONFIG as cfg

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

# roughly take 240 px for image dimensions
N_COLUMNS = int(cfg.UI_WIDTH / 240)
# keep a 15% margin
SQUARE_SIZE = int(cfg.UI_WIDTH / (N_COLUMNS * 1.15))


def generate_image_block(cocktail: Cocktail, mainscreen: MainScreen):
    """Generates a image block for the given cocktail"""
    button = QPushButton(cocktail.name)
    label = ClickableLabel(cocktail.name)
    cocktail_image = find_cocktail_image(cocktail)
    pixmap = QPixmap(str(cocktail_image))
    label.setPixmap(pixmap)
    label.setScaledContents(True)
    label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # type: ignore
    label.setMinimumSize(SQUARE_SIZE, SQUARE_SIZE)
    label.setMaximumSize(SQUARE_SIZE, SQUARE_SIZE)
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.addWidget(button)
    layout.addWidget(label)
    # take care of the button overload thingy, otherwise the first element will be a bool
    button.clicked.connect(
        lambda _, c=cocktail: mainscreen.open_cocktail_selection(c)
    )
    label.clicked.connect(
        lambda c=cocktail: mainscreen.open_cocktail_selection(c)
    )
    return layout


class CocktailView(QWidget):
    def __init__(self, mainscreen: MainScreen):
        super().__init__()
        self.scroll_area = QScrollArea()  # Create a QScrollArea
        self.scroll_area.setWidgetResizable(True)  # Make it resizable
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # type: ignore
        self.scroll_area.setFrameShadow(QFrame.Plain)  # type: ignore

        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(15)
        self.gridWidget = QWidget()  # Create a QWidget
        self.gridWidget.setLayout(self.grid)  # Set its layout to grid
        self.scroll_area.setWidget(self.gridWidget)  # Set the scroll area's widget to the QWidget with the grid layout

        self.vLayout = QVBoxLayout()
        self.vLayout.addWidget(self.scroll_area)
        self.setLayout(self.vLayout)

        self.mainscreen = mainscreen

    def populate_cocktails(self, cocktails: list[Cocktail]):
        """Adds the given cocktails to the grid"""
        # sort cocktails by name
        cocktails.sort(key=lambda x: x.name)
        for i in range(0, len(cocktails), N_COLUMNS):
            for j in range(N_COLUMNS):
                if i + j >= len(cocktails):
                    break
                block = generate_image_block(
                    cocktails[i + j],
                    self.mainscreen,
                )
                self.grid.addLayout(block, i // N_COLUMNS, j)

    def clear_cocktails(self):
        """Remove each cocktail from the grid"""
        while self.grid.count():
            child = self.grid.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
