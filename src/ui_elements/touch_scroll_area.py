from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QScrollArea

from .clickable_label import MAX_SCROLL_DISTANCE

# Adjust scrolling speed here
SCROLL_SPEED = 2.5


class TouchScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidgetResizable(True)
        self.mousePressPos = None
        self.pressed_scroll_bar_value = 0

    def mousePressEvent(self, event: QMouseEvent):  # ty:ignore[invalid-method-override]
        self.mousePressPos = event.pos()
        bar = self.verticalScrollBar()
        value = bar.value() if bar else 0
        self.pressed_scroll_bar_value = int(value)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):  # ty:ignore[invalid-method-override]
        if self.mousePressPos is None:
            return
        curPos = event.pos()
        moved = curPos - self.mousePressPos
        bar = self.verticalScrollBar()
        if bar:
            bar.setValue(int(self.pressed_scroll_bar_value - moved.y() * SCROLL_SPEED))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):  # ty:ignore[invalid-method-override]
        if self.mousePressPos is None:
            return
        moved = event.pos() - self.mousePressPos
        self.mouserPressPos = None
        if moved.manhattanLength() > MAX_SCROLL_DISTANCE:
            event.accept()
            return
        super().mouseReleaseEvent(event)
