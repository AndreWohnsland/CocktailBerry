import datetime
import traceback
import sys
from pathlib import Path
from itertools import cycle
import time

from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, QObject, pyqtSignal, QThreadPool
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView

from mainwindow import Ui_Leaderboard
from treemap import generate_treemap, get_plot_data
from html_template import gen_html


js_file = Path(__file__).parent.absolute() / "plotly-latest.min.js"


class Leaderboard(QMainWindow, Ui_Leaderboard):
    """ Opens the leaderboard """

    def __init__(self):
        super(Leaderboard, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.selectbtn.clicked.connect(lambda: self.update(getnext=True))
        self.options = cycle([1, 2, 3, 4])
        self.curr_option = next(self.options)

        self.data = get_plot_data(self.curr_option)
        self.fig = generate_treemap(self.data)
        self.browser = QWebEngineView(self)
        self.browser.setStyleSheet("body {background-color: rgb(14, 17, 23);}")
        html_fig = self.fig.to_html(include_plotlyjs=True, full_html=False, config={"displayModeBar": False})
        self.browser.setHtml(gen_html(html_fig))
        self.verticalLayout.addWidget(self.browser)
        self.time_label.setText(datetime.datetime.now().strftime('%H:%M'))

        # Spinning up a threadpool to constantly update
        self.threadpool = QThreadPool()
        self.start_worker()

    def update(self, getnext=False):
        if getnext:
            self.curr_option = next(self.options)
        data = get_plot_data(self.curr_option)
        # Only if other diagram, or data did change update plot
        if not self.data.equals(data):
            self.data = data
            self.fig = generate_treemap(self.data)
            html_fig = self.fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displayModeBar": False})
            self.browser.setHtml(gen_html(html_fig))
        self.time_label.setText(datetime.datetime.now().strftime('%H:%M'))
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
