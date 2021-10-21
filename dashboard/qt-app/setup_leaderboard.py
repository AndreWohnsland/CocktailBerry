import traceback
import sys
from itertools import cycle
import time
import matplotlib
from mainwindow import Ui_Leaderboard
# import datetime

from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, QObject, pyqtSignal, QThreadPool
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

        self.selectbtn.clicked.connect(lambda: self.update(getnext=True))
        self.options = cycle([1, 2, 3, 4])
        self.curr_option = next(self.options)

        self.fig = generate_figure(self.curr_option)
        self.canvas = FigureCanvas(self.fig)
        self.horizontalLayout.addWidget(self.canvas)

        # Spinning up a threadpool to constantly update
        self.threadpool = QThreadPool()
        self.start_worker()

    def update(self, getnext=False):
        # print(f"{datetime.datetime.now().strftime('%H:%M:%S')}: Update triggered with next {getnext}")
        self.canvas.figure.get_axes().clear()
        self.canvas.deleteLater()
        if getnext:
            self.curr_option = next(self.options)
        self.fig = generate_figure(self.curr_option)
        self.canvas = FigureCanvas(self.fig)
        self.horizontalLayout.addWidget(self.canvas)
        if not getnext:
            self.start_worker()

    def start_worker(self):
        """Starts a Worker with the timer, updates plot afterwards"""
        worker = Worker(self.update_intervall)
        worker.signals.finished.connect(self.update)
        self.threadpool.start(worker)

    def update_intervall(self):
        time.sleep(15)


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
