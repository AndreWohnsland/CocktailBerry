from PyQt5.QtWidgets import QMainWindow

from src import MAX_SUPPORTED_BOTTLES
from src.config.config_manager import CONFIG as cfg
from src.database_commander import DB_COMMANDER
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.tabs.bottles import set_fill_level_bars
from src.ui_elements.bottlewindow import Ui_Bottlewindow


class BottleWindow(QMainWindow, Ui_Bottlewindow):
    """Creates the Window to change to levels of the bottles."""

    def __init__(self, parent=None):
        """Init. Connects all the buttons, gets the names from Mainwindow/DB."""
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        # connects all the buttons
        self.PBAbbrechen.clicked.connect(self._cancel_clicked)
        self.PBEintragen.clicked.connect(self._enter_clicked)
        self.mainscreen = parent
        # Assigns the names to the labels
        # get all the DB values and assign the necessary to the level labels
        # note: since there can be blank bottles (id=0 so no match)
        # # this needs to be caught as well (no selection from D
        self.id_list = []
        self.max_volume = []
        self.assign_bottle_data()
        # creates lists of the objects and assigns functions later through a loop
        number = cfg.choose_bottle_number()
        myplus = [getattr(self, f"PBMplus{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        myminus = [getattr(self, f"PBMminus{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        mylabel = [getattr(self, f"LAmount{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        myname = [getattr(self, f"LName{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        max_buttons = [getattr(self, f"button_max_{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        min_buttons = [getattr(self, f"button_min_{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        max_labels = [getattr(self, f"label_max_volume_{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]
        volume_separators = [getattr(self, f"label_volume_separator_{x}") for x in range(1, MAX_SUPPORTED_BOTTLES + 1)]

        #  since zip only goes to the minimal of all, only one [:number] is needed
        zipped_data = zip(
            myplus,
            myminus,
            mylabel[:number],
            self.max_volume,
            max_buttons,
            min_buttons,
            max_labels,
        )
        min_allowed = 50
        change_value = 25
        for plus, minus, field, max_vol, max_button, min_button, max_label in zipped_data:
            plus.clicked.connect(
                lambda _, l=field, b=max_vol: DP_CONTROLLER.change_input_value(  # noqa: E741
                    label=l, minimal=min_allowed, maximal=b, delta=change_value
                )
            )
            minus.clicked.connect(
                lambda _, l=field, b=max_vol: DP_CONTROLLER.change_input_value(  # noqa: E741
                    label=l, minimal=min_allowed, maximal=b, delta=-change_value
                )
            )
            max_label.setText(str(max_vol))
            max_button.clicked.connect(lambda _, m=max_vol, f=field: f.setText(str(m)))
            min_button.clicked.connect(lambda _, f=field: f.setText(str(min_allowed)))

        # remove the elements exceeding the bottle number
        for elements in [myplus, myminus, mylabel, myname, max_buttons, min_buttons, max_labels, volume_separators]:
            for element in elements[number::]:
                element.deleteLater()

        UI_LANGUAGE.adjust_bottle_window(self)
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _cancel_clicked(self):
        """Close the Window without a change."""
        self.close()

    def _enter_clicked(self):
        """Enters the Data and closes the window."""
        number = cfg.choose_bottle_number()
        label_name = [getattr(self, f"LAmount{i}") for i in range(1, number + 1)]
        for label, ingredient_id, max_volume in zip(label_name, self.id_list, self.max_volume):
            new_amount = min(int(label.text()), max_volume)
            DB_COMMANDER.set_ingredient_level_to_value(ingredient_id, new_amount)
        set_fill_level_bars(self.mainscreen)
        self.close()

    def assign_bottle_data(self):
        number = cfg.choose_bottle_number()
        bottle_data = DB_COMMANDER.get_bottle_data_bottle_window()[:number]
        for i, (ingredient_name, bottle_level, ingredient_id, ingredient_volume) in enumerate(bottle_data, start=1):
            labelobj = getattr(self, f"LName{i}")
            label_name = getattr(self, f"LAmount{i}")
            if bottle_level is not None:
                label_name.setText(str(bottle_level))
                self.id_list.append(ingredient_id)
                self.max_volume.append(ingredient_volume)
                labelobj.setText(f"    {ingredient_name}")
            else:
                label_name.setText("0")
                self.id_list.append(0)
                self.max_volume.append(0)
                labelobj.setText("")
