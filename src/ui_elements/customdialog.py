# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\customdialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CustomDialog(object):
    def setupUi(self, CustomDialog):
        CustomDialog.setObjectName("CustomDialog")
        CustomDialog.resize(800, 480)
        CustomDialog.setStyleSheet("")
        self.verticalLayout = QtWidgets.QVBoxLayout(CustomDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.informationLabel = QtWidgets.QLabel(CustomDialog)
        self.informationLabel.setMinimumSize(QtCore.QSize(300, 100))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.informationLabel.setFont(font)
        self.informationLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.informationLabel.setWordWrap(True)
        self.informationLabel.setObjectName("informationLabel")
        self.verticalLayout.addWidget(self.informationLabel)
        self.closeButton = QtWidgets.QPushButton(CustomDialog)
        self.closeButton.setMinimumSize(QtCore.QSize(0, 50))
        self.closeButton.setMaximumSize(QtCore.QSize(16777215, 100))
        font = QtGui.QFont()
        font.setPointSize(30)
        self.closeButton.setFont(font)
        self.closeButton.setObjectName("closeButton")
        self.verticalLayout.addWidget(self.closeButton)

        self.retranslateUi(CustomDialog)
        QtCore.QMetaObject.connectSlotsByName(CustomDialog)

    def retranslateUi(self, CustomDialog):
        _translate = QtCore.QCoreApplication.translate
        CustomDialog.setWindowTitle(_translate("CustomDialog", "Information"))
        self.informationLabel.setText(_translate("CustomDialog", "Message Label which is really damn long"))
        self.closeButton.setText(_translate("CustomDialog", "Close"))
        self.closeButton.setProperty("cssClass", _translate("CustomDialog", "btn-inverted"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CustomDialog = QtWidgets.QDialog()
    ui = Ui_CustomDialog()
    ui.setupUi(CustomDialog)
    CustomDialog.show()
    sys.exit(app.exec_())
