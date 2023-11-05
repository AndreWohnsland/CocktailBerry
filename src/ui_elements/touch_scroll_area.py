from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtGui import QMouseEvent
from .clickable_label import MAX_SCROLL_DISTANCE

# Adjust scrolling speed here
SCROLL_SPEED = 2.5


class TouchScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidgetResizable(True)
        self.mousePressPos = None
        self.pressed_scroll_bar_value = 0

    def mousePressEvent(self, event: QMouseEvent):
        self.mousePressPos = event.pos()
        self.pressed_scroll_bar_value = int(self.verticalScrollBar().value())
        super(TouchScrollArea, self).mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mousePressPos is None:
            return
        curPos = event.pos()
        moved = curPos - self.mousePressPos  # type: ignore
        self.verticalScrollBar().setValue(int(self.pressed_scroll_bar_value - moved.y() * SCROLL_SPEED))
        super(TouchScrollArea, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.mousePressPos is None:
            return
        moved = event.pos() - self.mousePressPos  # type: ignore
        self.mouserPressPos = None
        if moved.manhattanLength() > MAX_SCROLL_DISTANCE:
            event.accept()
            return
        super(TouchScrollArea, self).mouseReleaseEvent(event)
