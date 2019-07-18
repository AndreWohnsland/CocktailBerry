# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'handadds.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_handadds(object):
    def setupUi(self, handadds):
        handadds.setObjectName("handadds")
        handadds.resize(400, 250)
        handadds.setMinimumSize(QtCore.QSize(400, 250))
        handadds.setMaximumSize(QtCore.QSize(400, 250))
        handadds.setStyleSheet("QWidget\n"
"{\n"
"    color: rgb(0, 123, 255);    \n"
"    background-color: rgb(0, 0, 0);\n"
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
"QPushButton:pressed\n"
"{\n"
"    color: rgb(255, 255, 255);    \n"
"    background-color: rgb(0, 123, 255);\n"
"    border-color: rgb(0, 123, 255);\n"
"}\n"
"\n"
"QPushButton:checked\n"
"{\n"
"    color: rgb(255, 255, 255);    \n"
"    background-color: rgb(0, 123, 255);\n"
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
"}\n"
"\n"
"QLineEdit\n"
"{\n"
"    padding: 1px;\n"
"    border-style: solid;\n"
"    border: 1px solid rgb(97, 97, 97);\n"
"    border-radius: 5;\n"
"}\n"
"\n"
"#Labbruch {\n"
"    color: rgb(239, 151, 0);\n"
"}")
        handadds.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(handadds)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.CBHandadd1 = QtWidgets.QComboBox(handadds)
        self.CBHandadd1.setMinimumSize(QtCore.QSize(200, 28))
        self.CBHandadd1.setMaximumSize(QtCore.QSize(200, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        self.CBHandadd1.setFont(font)
        self.CBHandadd1.setObjectName("CBHandadd1")
        self.verticalLayout_2.addWidget(self.CBHandadd1)
        self.CBHandadd2 = QtWidgets.QComboBox(handadds)
        self.CBHandadd2.setMinimumSize(QtCore.QSize(200, 28))
        self.CBHandadd2.setMaximumSize(QtCore.QSize(200, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        self.CBHandadd2.setFont(font)
        self.CBHandadd2.setObjectName("CBHandadd2")
        self.verticalLayout_2.addWidget(self.CBHandadd2)
        self.CBHandadd3 = QtWidgets.QComboBox(handadds)
        self.CBHandadd3.setMinimumSize(QtCore.QSize(200, 28))
        self.CBHandadd3.setMaximumSize(QtCore.QSize(200, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        self.CBHandadd3.setFont(font)
        self.CBHandadd3.setObjectName("CBHandadd3")
        self.verticalLayout_2.addWidget(self.CBHandadd3)
        self.CBHandadd4 = QtWidgets.QComboBox(handadds)
        self.CBHandadd4.setMinimumSize(QtCore.QSize(200, 28))
        self.CBHandadd4.setMaximumSize(QtCore.QSize(200, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        self.CBHandadd4.setFont(font)
        self.CBHandadd4.setObjectName("CBHandadd4")
        self.verticalLayout_2.addWidget(self.CBHandadd4)
        self.CBHandadd5 = QtWidgets.QComboBox(handadds)
        self.CBHandadd5.setMinimumSize(QtCore.QSize(200, 28))
        self.CBHandadd5.setMaximumSize(QtCore.QSize(200, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        self.CBHandadd5.setFont(font)
        self.CBHandadd5.setObjectName("CBHandadd5")
        self.verticalLayout_2.addWidget(self.CBHandadd5)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.LEHandadd1 = ClickableLineEdit(handadds)
        self.LEHandadd1.setMinimumSize(QtCore.QSize(0, 28))
        self.LEHandadd1.setMaximumSize(QtCore.QSize(100, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.LEHandadd1.setFont(font)
        self.LEHandadd1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LEHandadd1.setObjectName("LEHandadd1")
        self.verticalLayout_5.addWidget(self.LEHandadd1)
        self.LEHandadd2 = ClickableLineEdit(handadds)
        self.LEHandadd2.setMinimumSize(QtCore.QSize(0, 28))
        self.LEHandadd2.setMaximumSize(QtCore.QSize(100, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.LEHandadd2.setFont(font)
        self.LEHandadd2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LEHandadd2.setObjectName("LEHandadd2")
        self.verticalLayout_5.addWidget(self.LEHandadd2)
        self.LEHandadd3 = ClickableLineEdit(handadds)
        self.LEHandadd3.setMinimumSize(QtCore.QSize(0, 28))
        self.LEHandadd3.setMaximumSize(QtCore.QSize(100, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.LEHandadd3.setFont(font)
        self.LEHandadd3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LEHandadd3.setObjectName("LEHandadd3")
        self.verticalLayout_5.addWidget(self.LEHandadd3)
        self.LEHandadd4 = ClickableLineEdit(handadds)
        self.LEHandadd4.setMinimumSize(QtCore.QSize(0, 28))
        self.LEHandadd4.setMaximumSize(QtCore.QSize(100, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.LEHandadd4.setFont(font)
        self.LEHandadd4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LEHandadd4.setObjectName("LEHandadd4")
        self.verticalLayout_5.addWidget(self.LEHandadd4)
        self.LEHandadd5 = ClickableLineEdit(handadds)
        self.LEHandadd5.setMinimumSize(QtCore.QSize(0, 28))
        self.LEHandadd5.setMaximumSize(QtCore.QSize(100, 28))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.LEHandadd5.setFont(font)
        self.LEHandadd5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.LEHandadd5.setObjectName("LEHandadd5")
        self.verticalLayout_5.addWidget(self.LEHandadd5)
        self.horizontalLayout.addLayout(self.verticalLayout_5)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_11 = QtWidgets.QLabel(handadds)
        self.label_11.setMinimumSize(QtCore.QSize(60, 0))
        self.label_11.setMaximumSize(QtCore.QSize(60, 28))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.verticalLayout_3.addWidget(self.label_11)
        self.label_12 = QtWidgets.QLabel(handadds)
        self.label_12.setMinimumSize(QtCore.QSize(60, 0))
        self.label_12.setMaximumSize(QtCore.QSize(60, 28))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.verticalLayout_3.addWidget(self.label_12)
        self.label_13 = QtWidgets.QLabel(handadds)
        self.label_13.setMinimumSize(QtCore.QSize(60, 0))
        self.label_13.setMaximumSize(QtCore.QSize(60, 28))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label_13.setFont(font)
        self.label_13.setObjectName("label_13")
        self.verticalLayout_3.addWidget(self.label_13)
        self.label_15 = QtWidgets.QLabel(handadds)
        self.label_15.setMinimumSize(QtCore.QSize(60, 0))
        self.label_15.setMaximumSize(QtCore.QSize(60, 28))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label_15.setFont(font)
        self.label_15.setObjectName("label_15")
        self.verticalLayout_3.addWidget(self.label_15)
        self.label_14 = QtWidgets.QLabel(handadds)
        self.label_14.setMinimumSize(QtCore.QSize(60, 0))
        self.label_14.setMaximumSize(QtCore.QSize(60, 28))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(False)
        font.setWeight(50)
        self.label_14.setFont(font)
        self.label_14.setObjectName("label_14")
        self.verticalLayout_3.addWidget(self.label_14)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.PBEintragen = QtWidgets.QPushButton(handadds)
        self.PBEintragen.setMinimumSize(QtCore.QSize(200, 40))
        self.PBEintragen.setMaximumSize(QtCore.QSize(200, 16777215))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.PBEintragen.setFont(font)
        self.PBEintragen.setObjectName("PBEintragen")
        self.horizontalLayout_2.addWidget(self.PBEintragen)
        self.PBAbbrechen = QtWidgets.QPushButton(handadds)
        self.PBAbbrechen.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.PBAbbrechen.setFont(font)
        self.PBAbbrechen.setObjectName("PBAbbrechen")
        self.horizontalLayout_2.addWidget(self.PBAbbrechen)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(handadds)
        QtCore.QMetaObject.connectSlotsByName(handadds)

    def retranslateUi(self, handadds):
        _translate = QtCore.QCoreApplication.translate
        handadds.setWindowTitle(_translate("handadds", "Zutaten zum selbst hinzufügen"))
        self.label_11.setText(_translate("handadds", "ml"))
        self.label_12.setText(_translate("handadds", "ml"))
        self.label_13.setText(_translate("handadds", "ml"))
        self.label_15.setText(_translate("handadds", "ml"))
        self.label_14.setText(_translate("handadds", "ml"))
        self.PBEintragen.setText(_translate("handadds", "Eintragen"))
        self.PBAbbrechen.setText(_translate("handadds", "Abbrechen"))

from clickablelineedit import ClickableLineEdit

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    handadds = QtWidgets.QDialog()
    ui = Ui_handadds()
    ui.setupUi(handadds)
    handadds.show()
    sys.exit(app.exec_())

