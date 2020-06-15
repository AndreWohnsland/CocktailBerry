from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *

from ui_elements.bottlewindow import Ui_Bottlewindow

from src.supporter import plusminus
from src.bottles import Belegung_progressbar


class BottleWindow(QMainWindow, Ui_Bottlewindow):
    """ Creates the Window to change to levels of the bottles. """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons, gets the names from Mainwindow/DB. """
        super(BottleWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # connects all the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)
        # sets cursor visualibility and assigns the names to the labels
        self.ms = parent
        if not self.ms.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        for i in range(1, 11):
            CBBname = getattr(self.ms, "CBB" + str(i))
            labelobj = getattr(self, "LName" + str(i))
            labelobj.setText("    " + CBBname.currentText())
        self.DB = self.ms.DB
        self.c = self.ms.c
        # get all the DB values and assign the nececary to the level labels
        # note: since there can be blank bottles (id=0 so no match) this needs to be catched as well (no selection from DB)
        self.IDlist = []
        self.maxvolume = []
        for flasche in range(1, 11):
            bufferlevel = self.c.execute(
                "SELECT Zutaten.Mengenlevel, Zutaten.ID, Zutaten.Flaschenvolumen FROM Belegung INNER JOIN Zutaten ON Zutaten.ID = Belegung.ID AND Belegung.Flasche = ?",
                (flasche,),
            ).fetchone()
            LName = getattr(self, "LAmount" + str(flasche))
            if bufferlevel is not None:
                LName.setText(str(bufferlevel[0]))
                self.IDlist.append(bufferlevel[1])
                self.maxvolume.append(bufferlevel[2])
            else:
                LName.setText("0")
                self.IDlist.append(0)
                self.maxvolume.append(0)
        # creates lists of the objects and assings functions later through a loop
        myplus = [getattr(self, "PBMplus" + str(x)) for x in range(1, 11)]
        myminus = [getattr(self, "PBMminus" + str(x)) for x in range(1, 11)]
        mylabel = [getattr(self, "LAmount" + str(x)) for x in range(1, 11)]
        for plus, minus, field, vol in zip(myplus, myminus, mylabel, self.maxvolume):
            plus.clicked.connect(lambda _, l=field, b=vol: plusminus(label=l, operator="+", minimal=50, maximal=b, dm=25))
            minus.clicked.connect(lambda _, l=field, b=vol: plusminus(label=l, operator="-", minimal=50, maximal=b, dm=25))

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def eintragen_clicked(self):
        """ Enters the Data and closes the window. """
        for i in range(1, 11):
            LName = getattr(self, "LAmount" + str(i))
            new_amount = min(int(LName.text()), self.maxvolume[i - 1])
            self.c.execute(
                "UPDATE OR IGNORE Zutaten SET Mengenlevel = ? WHERE ID = ?", (new_amount, self.IDlist[i - 1]),
            )
        self.DB.commit()
        Belegung_progressbar(self.ms)
        self.close()
