import sys
from PyQt5.QtWidgets import QApplication

import src_ui.setup_mainwindow as setupui


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = setupui.MainScreen()
    w.showFullScreen()
    w.setFixedSize(800, 480)
    sys.exit(app.exec_())
