from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt

from src.ui_elements.bottlewindow import Ui_Bottlewindow

from src.config_manager import CONFIG as cfg
from src.tabs.bottles import set_fill_level_bars
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src import MAX_SUPPORTED_BOTTLES


class BottleWindow(QMainWindow, Ui_Bottlewindow):
    """ Creates the Window to change to levels of the bottles. """

    def __init__(self, parent=None):
        """ Init. Connects all the buttons, gets the names from Mainwindow/DB. """
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        DP_CONTROLLER.inject_stylesheet(self)
        # connects all the buttons
        self.PBAbbrechen.clicked.connect(self.abbrechen_clicked)
        self.PBEintragen.clicked.connect(self.eintragen_clicked)
        self.mainscreen = parent
        # Assigns the names to the labels
        # get all the DB values and assign the necessary to the level labels
        # note: since there can be blank bottles (id=0 so no match) this needs to be catched as well (no selection from DB)
        self.id_list = []
        self.maxvolume = []
        self.asign_bottle_data()
        # creates lists of the objects and assigns functions later through a loop
        number = cfg.choose_bottle_number()
        myplus = [getattr(self, f"PBMplus{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        myminus = [getattr(self, f"PBMminus{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        mylabel = [getattr(self, f"LAmount{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        myname = [getattr(self, f"LName{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]

        #  since zip only goes to the minimal of all, only one [:number] is needed
        for plus, minus, field, vol in zip(myplus, myminus, mylabel[:number], self.maxvolume):
            plus.clicked.connect(lambda _, l=field, b=vol: DP_CONTROLLER.plusminus(
                label=l, minimal=50, maximal=b, delta=25))
            minus.clicked.connect(lambda _, l=field, b=vol: DP_CONTROLLER.plusminus(
                label=l, minimal=50, maximal=b, delta=-25))

        # remove the elements exceeding the bottle number
        for elements in [myplus, myminus, mylabel, myname]:
            for element in elements[number::]:
                element.deleteLater()

        UI_LANGUAGE.adjust_bottle_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def abbrechen_clicked(self):
        """ Closes the Window without a change. """
        self.close()

    def eintragen_clicked(self):
        """ Enters the Data and closes the window. """
        number = cfg.choose_bottle_number()
        labelname = [getattr(self, f"LAmount{i}") for i in range(1, number + 1)]
        for label, ingredient_id, maxvolume in zip(labelname, self.id_list, self.maxvolume):
            new_amount = min(int(label.text()), maxvolume)
            DB_COMMANDER.set_ingredient_level_to_value(ingredient_id, new_amount)
        set_fill_level_bars(self.mainscreen)
        self.close()

    def asign_bottle_data(self):
        number = cfg.choose_bottle_number()
        bottle_data = DB_COMMANDER.get_bottle_data_bottle_window()[:number]
        for i, (ingredient_name, bottle_level, ingredient_id, ingredient_volume) in enumerate(bottle_data, start=1):
            labelobj = getattr(self, f"LName{i}")
            labelname = getattr(self, f"LAmount{i}")
            if bottle_level is not None:
                labelname.setText(str(bottle_level))
                self.id_list.append(ingredient_id)
                self.maxvolume.append(ingredient_volume)
                labelobj.setText(f"    {ingredient_name}")
            else:
                labelname.setText("0")
                self.id_list.append(0)
                self.maxvolume.append(0)
                labelobj.setText("")
