
from typing import List
from PyQt5.QtWidgets import QScrollArea, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton
from PyQt5.QtCore import Qt

from src.config_manager import ConfigManager
from src.ui_elements.clickablelineedit import ClickableLineEdit
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui.setup_password_screen import PasswordScreen


class ConfigWindow(QMainWindow, ConfigManager):
    def __init__(self):
        super().__init__()
        ConfigManager.__init__(self)
        self.icon_path = None
        self.config_objects = {}
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Change Configuration")
        self.scroll_area = QScrollArea()
        self.widget = QWidget()
        self.vbox = QVBoxLayout()

        for key, value in self.config_type.items():
            needed_type, check_fn_list = value
            self._choose_dispay_style(key, needed_type)

        self.button_back = QPushButton("Back")
        self.button_back.clicked.connect(self.close)
        self.button_save = QPushButton("Save")
        self.button_save.clicked.connect(self._save_config)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.button_back)
        self.hbox.addWidget(self.button_save)
        self.vbox.addLayout(self.hbox)

        self.widget.setLayout(self.vbox)

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.widget)
        self.setCentralWidget(self.scroll_area)

        self.show()

    def _save_config(self):
        print("TODO: Validation and Saving")
        print(self._retrieve_values())
        # self.close()

    def _choose_dispay_style(self, configname: str, configtype: type):
        """Creates the input face for the according config types"""
        # Add the elements header to the view
        self.vbox.addWidget(QLabel(f"{configname}, {configtype}"))
        # Reads out the current config value
        current_value = getattr(self, configname)
        # config_objects need to have the method to return the value of its type from the ui
        # Checking for Numbers
        if configtype == int:
            self._build_int_field(configname, current_value)
        # For Boolean only do a checkbox
        elif configtype == bool:
            self._buid_bool_field(configname, current_value)
        # for lists build up multiple elements
        elif configtype == list:
            self._build_list_field(configname, current_value)
        # Fallback default type for any not defined
        else:
            self._build_fallback_field(configname, current_value)

    def _build_int_field(self, configname, current_value):
        """Builds a field for integer input with numpad"""
        config_input = ClickableLineEdit(str(current_value))
        config_input.clicked.connect(lambda: PasswordScreen(self, le_to_write=config_input, headertext=configname))
        self.config_objects[configname] = lambda: int(config_input.text())
        self.vbox.addWidget(config_input)

    def _buid_bool_field(self, configname, current_value, displayed_text="on"):
        """Builds a field for bool input with a checkbox"""
        config_input = QCheckBox(displayed_text)
        config_input.setChecked(current_value)
        self.config_objects[configname] = config_input.isChecked
        self.vbox.addWidget(config_input)

    def _build_list_field(self, configname, current_value):
        """Builds a list of fields for a list input"""
        config_input = QVBoxLayout()
        list_values = []
        for initial_value in current_value:
            self._add_ui_element_to_list(initial_value, list_values, config_input)
        add_button = QPushButton("+ add")
        add_button.clicked.connect(lambda: self._add_ui_element_to_list("", list_values, config_input))
        v_container = QVBoxLayout()
        v_container.addLayout(config_input)
        v_container.addWidget(add_button)
        self.vbox.addLayout(v_container)
        self.config_objects[configname] = lambda: [x.text() for x in list_values]

    def _add_ui_element_to_list(self, initial_value, list_values: List, container):
        """Adds an additional input element for list buildup"""
        h_container = QHBoxLayout()
        remove_button = QPushButton("x")
        # the first argument in lambda is needed since the object reference within the loop
        remove_button.clicked.connect(lambda _, x=h_container: self._remove_ui_element_from_list(x, list_values))
        list_value = ClickableLineEdit(str(initial_value))
        list_value.clicked.connect(lambda: KeyboardWidget(self, list_value, 200))
        h_container.addWidget(list_value)
        h_container.addWidget(remove_button)
        container.addLayout(h_container)
        list_values.append(list_value)

    def _remove_ui_element_from_list(self, element, list_values: List):
        """Removed the referenced element from the ui"""
        for i in reversed(range(element.count())):
            found_widget = element.itemAt(i).widget()
            if found_widget in list_values:
                list_values.remove(found_widget)
            found_widget.setParent(None)
        element.deleteLater()

    def _build_fallback_field(self, configname, current_value):
        """builds the default input field for string input"""
        config_input = ClickableLineEdit(str(current_value))
        config_input.clicked.connect(lambda: KeyboardWidget(self, config_input, 200))
        self.config_objects[configname] = config_input.text
        self.vbox.addWidget(config_input)

    def _retrieve_values(self):
        return {key: getter() for key, getter in self.config_objects.items()}
