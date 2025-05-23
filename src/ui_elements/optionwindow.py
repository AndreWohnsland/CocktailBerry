# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\optionwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Optionwindow(object):
    def setupUi(self, Optionwindow):
        Optionwindow.setObjectName("Optionwindow")
        Optionwindow.resize(800, 480)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Optionwindow.sizePolicy().hasHeightForWidth())
        Optionwindow.setSizePolicy(sizePolicy)
        Optionwindow.setMinimumSize(QtCore.QSize(800, 480))
        Optionwindow.setMaximumSize(QtCore.QSize(800, 480))
        Optionwindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        Optionwindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(Optionwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scrollArea.setLineWidth(1)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, -223, 765, 770))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setContentsMargins(0, 0, 4, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.button_update_software = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_update_software.setMinimumSize(QtCore.QSize(0, 80))
        self.button_update_software.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_update_software.setFont(font)
        self.button_update_software.setObjectName("button_update_software")
        self.gridLayout_2.addWidget(self.button_update_software, 6, 0, 1, 2)
        self.button_check_internet = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_check_internet.setMinimumSize(QtCore.QSize(0, 80))
        self.button_check_internet.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_check_internet.setFont(font)
        self.button_check_internet.setObjectName("button_check_internet")
        self.gridLayout_2.addWidget(self.button_check_internet, 7, 1, 1, 1)
        self.button_reboot = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_reboot.setMinimumSize(QtCore.QSize(0, 80))
        self.button_reboot.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_reboot.setFont(font)
        self.button_reboot.setObjectName("button_reboot")
        self.gridLayout_2.addWidget(self.button_reboot, 3, 0, 1, 1)
        self.button_rfid = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_rfid.setEnabled(False)
        self.button_rfid.setMinimumSize(QtCore.QSize(0, 80))
        self.button_rfid.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_rfid.setFont(font)
        self.button_rfid.setObjectName("button_rfid")
        self.gridLayout_2.addWidget(self.button_rfid, 8, 1, 1, 1)
        self.button_backup = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_backup.setMinimumSize(QtCore.QSize(0, 80))
        self.button_backup.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_backup.setFont(font)
        self.button_backup.setObjectName("button_backup")
        self.gridLayout_2.addWidget(self.button_backup, 2, 0, 1, 1)
        self.button_clean = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_clean.setMinimumSize(QtCore.QSize(0, 80))
        self.button_clean.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_clean.setFont(font)
        self.button_clean.setObjectName("button_clean")
        self.gridLayout_2.addWidget(self.button_clean, 0, 0, 1, 1)
        self.button_shutdown = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_shutdown.setMinimumSize(QtCore.QSize(0, 80))
        self.button_shutdown.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_shutdown.setFont(font)
        self.button_shutdown.setObjectName("button_shutdown")
        self.gridLayout_2.addWidget(self.button_shutdown, 3, 1, 1, 1)
        self.button_restore = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_restore.setMinimumSize(QtCore.QSize(0, 80))
        self.button_restore.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_restore.setFont(font)
        self.button_restore.setObjectName("button_restore")
        self.gridLayout_2.addWidget(self.button_restore, 2, 1, 1, 1)
        self.button_wifi = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_wifi.setMinimumSize(QtCore.QSize(0, 80))
        self.button_wifi.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_wifi.setFont(font)
        self.button_wifi.setObjectName("button_wifi")
        self.gridLayout_2.addWidget(self.button_wifi, 7, 0, 1, 1)
        self.button_config = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_config.setMinimumSize(QtCore.QSize(0, 80))
        self.button_config.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_config.setFont(font)
        self.button_config.setObjectName("button_config")
        self.gridLayout_2.addWidget(self.button_config, 1, 0, 1, 1)
        self.button_addons = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_addons.setMinimumSize(QtCore.QSize(0, 80))
        self.button_addons.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_addons.setFont(font)
        self.button_addons.setObjectName("button_addons")
        self.gridLayout_2.addWidget(self.button_addons, 8, 0, 1, 1)
        self.button_update_system = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_update_system.setMinimumSize(QtCore.QSize(0, 80))
        self.button_update_system.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_update_system.setFont(font)
        self.button_update_system.setObjectName("button_update_system")
        self.gridLayout_2.addWidget(self.button_update_system, 4, 1, 1, 1)
        self.button_export = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_export.setMinimumSize(QtCore.QSize(0, 80))
        self.button_export.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_export.setFont(font)
        self.button_export.setObjectName("button_export")
        self.gridLayout_2.addWidget(self.button_export, 1, 1, 1, 1)
        self.button_logs = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_logs.setMinimumSize(QtCore.QSize(0, 80))
        self.button_logs.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_logs.setFont(font)
        self.button_logs.setObjectName("button_logs")
        self.gridLayout_2.addWidget(self.button_logs, 4, 0, 1, 1)
        self.button_calibration = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_calibration.setMinimumSize(QtCore.QSize(0, 80))
        self.button_calibration.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_calibration.setFont(font)
        self.button_calibration.setObjectName("button_calibration")
        self.gridLayout_2.addWidget(self.button_calibration, 0, 1, 1, 1)
        self.button_resources = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.button_resources.setMinimumSize(QtCore.QSize(0, 80))
        self.button_resources.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_resources.setFont(font)
        self.button_resources.setObjectName("button_resources")
        self.gridLayout_2.addWidget(self.button_resources, 5, 0, 1, 2)
        self.verticalLayout_3.addLayout(self.gridLayout_2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 4, 0, 1, 1)
        self.button_back = QtWidgets.QPushButton(self.centralwidget)
        self.button_back.setMinimumSize(QtCore.QSize(0, 80))
        self.button_back.setMaximumSize(QtCore.QSize(5000, 300))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_back.setFont(font)
        self.button_back.setObjectName("button_back")
        self.gridLayout.addWidget(self.button_back, 5, 0, 1, 1)
        Optionwindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(Optionwindow)
        QtCore.QMetaObject.connectSlotsByName(Optionwindow)

    def retranslateUi(self, Optionwindow):
        _translate = QtCore.QCoreApplication.translate
        Optionwindow.setWindowTitle(_translate("Optionwindow", "Options"))
        self.button_update_software.setText(_translate("Optionwindow", "Update CocktailBerry Software"))
        self.button_check_internet.setText(_translate("Optionwindow", "Check Internet"))
        self.button_reboot.setText(_translate("Optionwindow", "Reboot"))
        self.button_rfid.setText(_translate("Optionwindow", "Write RFID"))
        self.button_backup.setText(_translate("Optionwindow", "Backup"))
        self.button_clean.setText(_translate("Optionwindow", "Cleaning"))
        self.button_shutdown.setText(_translate("Optionwindow", "Shutdown"))
        self.button_restore.setText(_translate("Optionwindow", "Restore"))
        self.button_wifi.setText(_translate("Optionwindow", "WiFi"))
        self.button_config.setText(_translate("Optionwindow", "Change Config"))
        self.button_addons.setText(_translate("Optionwindow", "Addons"))
        self.button_update_system.setText(_translate("Optionwindow", "Update System"))
        self.button_export.setText(_translate("Optionwindow", "Export"))
        self.button_logs.setText(_translate("Optionwindow", "Logs"))
        self.button_calibration.setText(_translate("Optionwindow", "Calibration"))
        self.button_resources.setText(_translate("Optionwindow", "System Resource Usage"))
        self.button_back.setText(_translate("Optionwindow", "< Back"))
        self.button_back.setProperty("cssClass", _translate("Optionwindow", "btn-inverted"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Optionwindow = QtWidgets.QMainWindow()
    ui = Ui_Optionwindow()
    ui.setupUi(Optionwindow)
    Optionwindow.show()
    sys.exit(app.exec_())
