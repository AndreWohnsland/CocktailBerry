from itertools import cycle
import time
import matplotlib
from mainwindow import Ui_Leaderboard

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, qApp

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from waffle import generate_figure

matplotlib.use('Qt5Agg')


class Leaderboard(QMainWindow, Ui_Leaderboard):
    """ Opens the leaderboard """

    def __init__(self):
        super(Leaderboard, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.selectbtn.clicked.connect(self.select)
        self.options = cycle([1, 2, 3, 4])
        self.curr_option = next(self.options)

        fig = generate_figure(self.curr_option)
        self.canvas = FigureCanvas(fig)
        self.horizontalLayout.addWidget(self.canvas)

    def select(self):
        self.canvas.deleteLater()
        self.curr_option = next(self.options)
        self.canvas = FigureCanvas(generate_figure(self.curr_option))
        self.horizontalLayout.addWidget(self.canvas)

    def update(self, timing=15):
        self.canvas.deleteLater()
        self.canvas = FigureCanvas(generate_figure(self.curr_option))
        self.horizontalLayout.addWidget(self.canvas)
        time.sleep(timing)
        qApp.processEvents()
