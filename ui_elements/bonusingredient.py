# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bonusingredient.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_addingredient(object):
    def setupUi(self, addingredient):
        addingredient.setObjectName("addingredient")
        addingredient.resize(400, 350)
        addingredient.setMinimumSize(QtCore.QSize(400, 350))
        addingredient.setMaximumSize(QtCore.QSize(400, 350))
        addingredient.setStyleSheet("QWidget\n"
"{\n"
"    color: rgb(0, 123, 255);    \n"
"    background-color: rgb(0, 0, 0);\n"
"}\n"
"\n"
"QPushButton {\n"
"    background-color: rgb(0, 0, 0);\n"
"    color: (0, 123, 255);\n"
"    border-width: 4px;\n"
"    border-color: rgb(0, 123, 255);\n"
"    border-style: solid;\n"
"    border-radius: 7;\n"
"    padding: 3px;\n"
"    padding-left: 5px;\n"
"    padding-right: 5px;\n"
"}\n"
"\n"
"QPushButton:pressed\n"
"{\n"
"    color: rgb(239, 151, 0);    \n"
"    border-color: rgb(239, 151, 0);\n"
"}\n"
"\n"
"#LAmount{\n"
"    color: rgb(239, 151, 0);\n"
"}\n"
"\n"
"QComboBox {\n"
"    color: rgb(0, 123, 255);    \n"
"    border: 1px solid  rgb(97, 97, 97);\n"
"    border-top-left-radius: 7px;\n"
"    border-bottom-left-radius: 7px;\n"
"    padding: 1px 18px 1px 5px;\n"
"    min-width: 6em;\n"
"}\n"
"\n"
"QComboBox:on { /* shift the text when the popup opens */\n"
"    border: 1px solid  rgb(97, 97, 97);\n"
"    border-top-left-radius: 7px;\n"
"    border-bottom-left-radius: 0px;\n"
"    color: rgb(239, 151, 0);\n"
"}")
        addingredient.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(addingredient)
        self.verticalLayout.setObjectName("verticalLayout")
        self.CBingredient = QtWidgets.QComboBox(addingredient)
        self.CBingredient.setMinimumSize(QtCore.QSize(103, 29))
        self.CBingredient.setMaximumSize(QtCore.QSize(500, 80))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.CBingredient.setFont(font)
        self.CBingredient.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.CBingredient.setMaxVisibleItems(10)
        self.CBingredient.setObjectName("CBingredient")
        self.verticalLayout.addWidget(self.CBingredient)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.PBminus = QtWidgets.QPushButton(addingredient)
        self.PBminus.setMinimumSize(QtCore.QSize(60, 18))
        self.PBminus.setMaximumSize(QtCore.QSize(100, 100))
        font = QtGui.QFont()
        font.setPointSize(36)
        font.setBold(True)
        font.setWeight(75)
        self.PBminus.setFont(font)
        self.PBminus.setObjectName("PBminus")
        self.horizontalLayout.addWidget(self.PBminus)
        self.LAmount = QtWidgets.QLabel(addingredient)
        self.LAmount.setMinimumSize(QtCore.QSize(65, 0))
        self.LAmount.setMaximumSize(QtCore.QSize(175, 100))
        font = QtGui.QFont()
        font.setPointSize(36)
        font.setBold(True)
        font.setWeight(75)
        self.LAmount.setFont(font)
        self.LAmount.setLineWidth(1)
        self.LAmount.setAlignment(QtCore.Qt.AlignCenter)
        self.LAmount.setObjectName("LAmount")
        self.horizontalLayout.addWidget(self.LAmount)
        self.PBplus = QtWidgets.QPushButton(addingredient)
        self.PBplus.setMinimumSize(QtCore.QSize(60, 18))
        self.PBplus.setMaximumSize(QtCore.QSize(100, 100))
        font = QtGui.QFont()
        font.setPointSize(36)
        font.setBold(True)
        font.setWeight(75)
        self.PBplus.setFont(font)
        self.PBplus.setObjectName("PBplus")
        self.horizontalLayout.addWidget(self.PBplus)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.PBAbbrechen = QtWidgets.QPushButton(addingredient)
        self.PBAbbrechen.setMinimumSize(QtCore.QSize(0, 70))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.PBAbbrechen.setFont(font)
        self.PBAbbrechen.setObjectName("PBAbbrechen")
        self.verticalLayout.addWidget(self.PBAbbrechen)
        self.PBAusgeben = QtWidgets.QPushButton(addingredient)
        self.PBAusgeben.setMinimumSize(QtCore.QSize(0, 70))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.PBAusgeben.setFont(font)
        self.PBAusgeben.setObjectName("PBAusgeben")
        self.verticalLayout.addWidget(self.PBAusgeben)

        self.retranslateUi(addingredient)
        QtCore.QMetaObject.connectSlotsByName(addingredient)

    def retranslateUi(self, addingredient):
        _translate = QtCore.QCoreApplication.translate
        addingredient.setWindowTitle(_translate("addingredient", "Zutatenausgabe auswählen"))
        self.PBminus.setText(_translate("addingredient", "-"))
        self.LAmount.setText(_translate("addingredient", "50"))
        self.PBplus.setText(_translate("addingredient", "+"))
        self.PBAbbrechen.setText(_translate("addingredient", "Abbrechen"))
        self.PBAusgeben.setText(_translate("addingredient", "Ausgeben"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    addingredient = QtWidgets.QDialog()
    ui = Ui_addingredient()
    ui.setupUi(addingredient)
    addingredient.show()
    sys.exit(app.exec_())

