import sys
from PyQt5.QtWidgets import QApplication

from setup_leaderboard import Leaderboard


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Leaderboard()
    w.showFullScreen()
    sys.exit(app.exec_())
