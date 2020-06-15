from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import *
from PyQt5.uic import *
import time

from ui_elements.bonusingredient import Ui_addingredient

from src.supporter import plusminus
from src.display_handler import DisplayHandler

display_handler = DisplayHandler()


class GetIngredientWindow(QDialog, Ui_addingredient):
    """ Creates a Dialog to chose an additional ingredient and the amount
    to spend this ingredient.
    """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons and get values for the Combobox. """
        super(GetIngredientWindow, self).__init__(parent)
        self.setupUi(self)
        # Set window properties
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon(parent.icon_path))
        self.ms = parent
        if not self.ms.DEVENVIRONMENT:
            self.setCursor(Qt.BlankCursor)
        # Connect all the buttons
        self.PBplus.clicked.connect(lambda: plusminus(self.LAmount, "+", 20, 100, 10))
        self.PBminus.clicked.connect(lambda: plusminus(self.LAmount, "-", 20, 100, 10))
        self.PBAusgeben.clicked.connect(self.ausgeben_clicked)
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        # Get the DB and fill Combobox
        self.DB = self.ms.DB
        self.c = self.ms.c
        bottles = self.c.execute("SELECT Zutaten.Name FROM Zutaten INNER JOIN Belegung ON Zutaten.ID = Belegung.ID")
        for bottle in bottles:
            self.CBingredient.addItem(bottle[0])

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def ausgeben_clicked(self):
        """ Calls the Progressbarwindow and spends the given amount of the ingredient. """
        # get the globals, set GPIO
        import globals

        if not self.ms.DEVENVIRONMENT:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)

        timestep = 0.05
        pins = globals.USEDPINS
        volumeflows = globals.PUMP_VOLUMEFLOW
        globals.loopcheck = True
        # select the bottle and the according pin as well as Volumeflow, calculates the needed time
        bottlename = self.CBingredient.currentText()
        bottle = self.c.execute("SELECT Flasche From Belegung WHERE Zutat_F = ?", (bottlename,)).fetchone()
        if bottle is not None:
            pos = bottle[0] - 1
            print(f"Ausgabemenge von {self.CBingredient.currentText()}: {self.LAmount.text()} die Flaschennummer ist: {pos + 1}")
        pin = pins[pos]
        volumeflow = int(volumeflows[pos])
        volume = int(self.LAmount.text())
        check = True
        # now checks if there is enough of the ingredient
        amounttest = self.c.execute("SELECT Mengenlevel FROM Zutaten WHERE Name = ? and Mengenlevel < ?", (bottlename, volume),).fetchone()
        if amounttest is not None:
            missingamount = amounttest[0]
            display_handler.standard_box(
                f"Die Flasche hat nicht genug Volumen! {volume} ml werden gebraucht, {missingamount} ml sind vorhanden!"
            )
            check = False
        if check:
            time_needed = volume / volumeflow
            time_actual = 0
            # initialise and open the Pins = activate the pump
            if not self.ms.DEVENVIRONMENT:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, 0)
            print(f"Pin: {pin} wurde initialisiert!")
            self.close()
            self.ms.progressionqwindow(labelchange="Zutat wird ausgegeben!\nFortschritt:")
            # until the time is reached, or the process is interrupted loop:
            while time_actual < time_needed and globals.loopcheck:
                if (time_actual) % 1 == 0:
                    print(str(time_actual) + " von " + str(time_needed) + " Sekunden ")
                time_actual += timestep
                time_actual = round(time_actual, 2)
                time.sleep(timestep)
                self.ms.prow_change(time_actual / time_needed * 100)
                qApp.processEvents()
            # close the pin / pump at the end of the process.
            if not self.ms.DEVENVIRONMENT:
                GPIO.output(pin, 1)
            # checks if the program was interrupted before or carried out till the end, gets the used volume
            if not globals.loopcheck:
                volume_to_substract = int(round(time_actual * volumeflow, 0))
            else:
                volume_to_substract = volume
            # substract the volume from the DB
            self.c.execute(
                "UPDATE OR IGNORE Zutaten SET Mengenlevel = Mengenlevel - ?, Verbrauchsmenge = Verbrauchsmenge + ?, Verbrauch = Verbrauch + ?  WHERE Name = ?",
                (volume_to_substract, volume_to_substract, volume_to_substract, bottlename,),
            )
            self.DB.commit()
            self.ms.prow_close()
