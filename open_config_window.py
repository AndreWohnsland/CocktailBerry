import sys
from PyQt5 import QtWidgets
from src.ui.create_config_window import ConfigWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = ConfigWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
