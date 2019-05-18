# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'progressbarwindow.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Progressbarwindow(object):
    def setupUi(self, Progressbarwindow):
        Progressbarwindow.setObjectName("Progressbarwindow")
        Progressbarwindow.resize(600, 360)
        Progressbarwindow.setMinimumSize(QtCore.QSize(600, 360))
        Progressbarwindow.setMaximumSize(QtCore.QSize(600, 360))
        Progressbarwindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        Progressbarwindow.setStyleSheet("QWidget\n"
"{\n"
"    color: rgb(0, 123, 255);    \n"
"    background-color: rgb(0, 0, 0);\n"
"\n"
"}\n"
"\n"
"QPushButton {\n"
"    background-color: rgb(97, 97, 97);\n"
"    color: rgb(255, 255, 255);\n"
"    border-width: 1px;\n"
"    border-color: rgb(97, 97, 97);\n"
"    border-style: solid;\n"
"    border-radius: 7;\n"
"    padding: 3px;\n"
"    padding-left: 5px;\n"
"    padding-right: 5px;\n"
"}\n"
"\n"
"QPushButton:checked\n"
"{\n"
"    color: rgb(255, 255, 255);    \n"
"    background-color: rgb(0, 123, 255);\n"
"}\n"
"\n"
"QProgressBar\n"
"{\n"
"    background-color: rgb(166, 166, 166);\n"
"    color: rgb(0, 0, 0);\n"
"    border: 2px rgb(166, 166, 166);\n"
"    border-radius: 5px;\n"
"}\n"
"\n"
"QProgressBar::chunk {\n"
"    border: 2px rgb(166, 166, 166);\n"
"    border-top-left-radius: 5px;\n"
"    border-bottom-left-radius: 5px;\n"
"    border-top-right-radius: 5px;\n"
"    border-bottom-right-radius: 5px;\n"
"    background-color: rgb(0, 123, 255);\n"
"   /* width: 40px;\n"
"    margin: 0.5px;*/\n"
"}\n"
"\n"
"#Labbruch {\n"
"    color: rgb(239, 151, 0);\n"
"}")
        self.centralwidget = QtWidgets.QWidget(Progressbarwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.Lheader = QtWidgets.QLabel(self.centralwidget)
        self.Lheader.setMaximumSize(QtCore.QSize(16777215, 120))
        font = QtGui.QFont()
        font.setPointSize(26)
        font.setBold(True)
        font.setWeight(75)
        self.Lheader.setFont(font)
        self.Lheader.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.Lheader.setObjectName("Lheader")
        self.verticalLayout.addWidget(self.Lheader)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setMaximumSize(QtCore.QSize(16777215, 60))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setTextVisible(False)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.Labbruch = QtWidgets.QLabel(self.centralwidget)
        self.Labbruch.setMaximumSize(QtCore.QSize(16777215, 60))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.Labbruch.setFont(font)
        self.Labbruch.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.Labbruch.setObjectName("Labbruch")
        self.verticalLayout.addWidget(self.Labbruch)
        self.PBabbrechen = QtWidgets.QPushButton(self.centralwidget)
        self.PBabbrechen.setMinimumSize(QtCore.QSize(0, 100))
        font = QtGui.QFont()
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.PBabbrechen.setFont(font)
        self.PBabbrechen.setObjectName("PBabbrechen")
        self.verticalLayout.addWidget(self.PBabbrechen)
        Progressbarwindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(Progressbarwindow)
        QtCore.QMetaObject.connectSlotsByName(Progressbarwindow)

    def retranslateUi(self, Progressbarwindow):
        _translate = QtCore.QCoreApplication.translate
        Progressbarwindow.setWindowTitle(_translate("Progressbarwindow", "~~ Cocktail wird zubereitet ~~"))
        self.Lheader.setText(_translate("Progressbarwindow", "<html><head/><body><p>Cocktail wird zubereitet!</p><p><span style=\" color:#ef9700;\">Fortschritt:</span></p></body></html>"))
        self.progressBar.setFormat(_translate("Progressbarwindow", "%p%"))
        self.Labbruch.setText(_translate("Progressbarwindow", "Der Cocktail kann auch abgebrochen werden"))
        self.PBabbrechen.setText(_translate("Progressbarwindow", "Abbrechen"))

