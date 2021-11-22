from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QTabWidget, QTabBar


class ScaleableTabBar(QTabBar):
    def tabSizeHint(self, index):
        size = QTabBar.tabSizeHint(self, index)
        w = int(self.width() / self.count())
        return QSize(w, size.height())


class ScaleableTab(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.setTabBar(ScaleableTabBar())

    def tabBar(self):
        return ScaleableTabBar()
