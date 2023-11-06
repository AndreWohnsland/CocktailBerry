# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\picture_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PictureWindow(object):
    def setupUi(self, PictureWindow):
        PictureWindow.setObjectName("PictureWindow")
        PictureWindow.resize(800, 480)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PictureWindow.sizePolicy().hasHeightForWidth())
        PictureWindow.setSizePolicy(sizePolicy)
        PictureWindow.setMinimumSize(QtCore.QSize(800, 480))
        PictureWindow.setMaximumSize(QtCore.QSize(800, 480))
        PictureWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        PictureWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(PictureWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.button_back = QtWidgets.QPushButton(self.centralwidget)
        self.button_back.setMinimumSize(QtCore.QSize(0, 80))
        self.button_back.setMaximumSize(QtCore.QSize(5000, 80))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_back.setFont(font)
        self.button_back.setObjectName("button_back")
        self.gridLayout.addWidget(self.button_back, 4, 0, 1, 1)
        self.button_enter = QtWidgets.QPushButton(self.centralwidget)
        self.button_enter.setMinimumSize(QtCore.QSize(0, 80))
        self.button_enter.setMaximumSize(QtCore.QSize(5000, 80))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_enter.setFont(font)
        self.button_enter.setObjectName("button_enter")
        self.gridLayout.addWidget(self.button_enter, 4, 3, 1, 1)
        self.label_titel = QtWidgets.QLabel(self.centralwidget)
        self.label_titel.setMaximumSize(QtCore.QSize(16777215, 40))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label_titel.setFont(font)
        self.label_titel.setAlignment(QtCore.Qt.AlignCenter)
        self.label_titel.setObjectName("label_titel")
        self.gridLayout.addWidget(self.label_titel, 0, 0, 1, 4)
        self.button_upload = QtWidgets.QPushButton(self.centralwidget)
        self.button_upload.setMinimumSize(QtCore.QSize(0, 80))
        self.button_upload.setMaximumSize(QtCore.QSize(80, 80))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_upload.setFont(font)
        self.button_upload.setObjectName("button_upload")
        self.gridLayout.addWidget(self.button_upload, 4, 2, 1, 1)
        self.button_remove = QtWidgets.QPushButton(self.centralwidget)
        self.button_remove.setMinimumSize(QtCore.QSize(0, 80))
        self.button_remove.setMaximumSize(QtCore.QSize(80, 80))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.button_remove.setFont(font)
        self.button_remove.setObjectName("button_remove")
        self.gridLayout.addWidget(self.button_remove, 4, 1, 1, 1)
        self.picture_system = QtWidgets.QLabel(self.centralwidget)
        self.picture_system.setScaledContents(True)
        self.picture_system.setAlignment(QtCore.Qt.AlignCenter)
        self.picture_system.setObjectName("picture_system")
        self.gridLayout.addWidget(self.picture_system, 2, 2, 1, 2)
        self.picture_user = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(22)
        self.picture_user.setFont(font)
        self.picture_user.setScaledContents(True)
        self.picture_user.setAlignment(QtCore.Qt.AlignCenter)
        self.picture_user.setObjectName("picture_user")
        self.gridLayout.addWidget(self.picture_user, 2, 0, 1, 2)
        self.label_user = QtWidgets.QLabel(self.centralwidget)
        self.label_user.setMaximumSize(QtCore.QSize(16777215, 28))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_user.setFont(font)
        self.label_user.setAlignment(QtCore.Qt.AlignCenter)
        self.label_user.setObjectName("label_user")
        self.gridLayout.addWidget(self.label_user, 1, 0, 1, 2)
        self.label_system = QtWidgets.QLabel(self.centralwidget)
        self.label_system.setMaximumSize(QtCore.QSize(16777215, 28))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_system.setFont(font)
        self.label_system.setAlignment(QtCore.Qt.AlignCenter)
        self.label_system.setObjectName("label_system")
        self.gridLayout.addWidget(self.label_system, 1, 2, 1, 2)
        PictureWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(PictureWindow)
        QtCore.QMetaObject.connectSlotsByName(PictureWindow)

    def retranslateUi(self, PictureWindow):
        _translate = QtCore.QCoreApplication.translate
        PictureWindow.setWindowTitle(_translate("PictureWindow", "Set Cocktail Picture"))
        self.button_back.setText(_translate("PictureWindow", "< Back"))
        self.button_enter.setText(_translate("PictureWindow", "Enter"))
        self.button_enter.setProperty("cssClass", _translate("PictureWindow", "btn-inverted"))
        self.label_titel.setText(_translate("PictureWindow", "Label for picture set + Name"))
        self.label_titel.setProperty("cssClass", _translate("PictureWindow", "secondary bold"))
        self.button_upload.setText(_translate("PictureWindow", "+"))
        self.button_upload.setProperty("cssClass", _translate("PictureWindow", "btn-inverted neutral"))
        self.button_remove.setText(_translate("PictureWindow", "R"))
        self.button_remove.setProperty("cssClass", _translate("PictureWindow", "btn-inverted destructive"))
        self.picture_system.setText(_translate("PictureWindow", "System Image"))
        self.picture_user.setText(_translate("PictureWindow", "<html><head/><body><p>No Image</p><p>Available</p></body></html>"))
        self.picture_user.setProperty("cssClass", _translate("PictureWindow", "neutral"))
        self.label_user.setText(_translate("PictureWindow", "User"))
        self.label_system.setText(_translate("PictureWindow", "System"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    PictureWindow = QtWidgets.QMainWindow()
    ui = Ui_PictureWindow()
    ui.setupUi(PictureWindow)
    PictureWindow.show()
    sys.exit(app.exec_())