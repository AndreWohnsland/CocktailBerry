
import matplotlib
from mainwindow import Ui_Leaderboard

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
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

        self.canvas = FigureCanvas(generate_figure("TEST"))
        self.horizontalLayout.addWidget(self.canvas)

    def select(self):
        print("clicked")
        self.canvas.deleteLater()
        self.canvas = FigureCanvas(generate_figure("Clicked"))
        self.horizontalLayout.addWidget(self.canvas)
