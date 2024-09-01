from typing import Any, Callable, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
)

from src.config.config_types import ConfigClass, ConfigInterface, DictType, ListType
from src.config.errors import ConfigError
from src.config_manager import CONFIG as cfg
from src.config_manager import ChooseType
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui.creation_utils import LARGE_FONT, MEDIUM_FONT, SMALL_FONT, adjust_font, create_spacer
from src.ui.setup_color_window import ColorWindow
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui.setup_numpad_widget import NumpadWidget
from src.ui_elements import Ui_ConfigWindow
from src.ui_elements.clickablelineedit import ClickableLineEdit
from src.utils import restart_program


class ConfigWindow(QMainWindow, Ui_ConfigWindow):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        self.config_objects = {}
        self.color_window: Optional[ColorWindow] = None
        self.button_custom_color: Optional[QPushButton] = None
        UI_LANGUAGE.adjust_config_window(self)
        self._init_ui()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _init_ui(self):
        # adds all the configs to the window
        for key, config_setting in cfg.config_type.items():
            self._choose_display_style(key, config_setting)

        self.button_save.clicked.connect(self._save_config)
        self.button_back.clicked.connect(self.close)
        # other window may have little elements and spacing is bad,
        # so add a spacer to the end
        self.vbox_other.addItem(create_spacer(1, expand=True))

    def _save_config(self):
        try:
            cfg.validate_and_set_config(self._retrieve_values())
            cfg.sync_config_to_file()
        except ConfigError as err:
            DP_CONTROLLER.say_wrong_config(str(err))
            return
        # Also asks if to restart program to get new config
        if DP_CONTROLLER.ask_to_restart_for_config():
            restart_program()
        self.close()

    def _choose_display_style(self, config_name: str, config_setting: ConfigInterface):
        """Create the input face for the according config types."""
        # Add the elements header to the view
        header = QLabel(f"{config_name}:")
        adjust_font(header, LARGE_FONT, True)
        vbox = self._choose_tab_container(config_name)
        vbox.addWidget(header)
        description_text = UI_LANGUAGE.get_config_description(config_name)
        if description_text:
            description = QLabel(description_text)
            description.setWordWrap(True)
            adjust_font(description, SMALL_FONT)
            vbox.addWidget(description)
        # Reads out the current config value
        current_value = getattr(cfg, config_name)
        getter_fn = self._build_input_field(config_name, config_setting, current_value)
        # assigning the getter function for the config into the dict
        self.config_objects[config_name] = getter_fn
        if config_name == "MAKER_THEME":
            self._build_custom_color_button(vbox)
        # Add small spacer after each section
        vbox.addItem(create_spacer(12))

    def _build_custom_color_button(self, vbox: QVBoxLayout):
        """Build a button to edit custom theme."""
        self.button_custom_color = QPushButton("Define Custom Color")
        self.button_custom_color.setMaximumSize(QSize(16777215, 200))
        self.button_custom_color.setMinimumSize(QSize(0, 50))
        adjust_font(self.button_custom_color, LARGE_FONT, True)
        self.button_custom_color.clicked.connect(self._open_color_window)  # type: ignore
        vbox.addWidget(self.button_custom_color)

    def _open_color_window(self):
        self.color_window = ColorWindow(self.mainscreen)

    def _build_input_field(
        self, config_name: str, config_setting: ConfigInterface, current_value: Any, layout: Optional[QBoxLayout] = None
    ):
        """Build the input field and returns its getter function."""
        if layout is None:
            layout = self._choose_tab_container(config_name)
        config_type = config_setting.ui_type
        if config_type is int:
            return self._build_int_field(layout, config_name, current_value)
        if config_type is float:
            return self._build_float_field(layout, config_name, current_value)
        if config_type is bool:
            return self._build_bool_field(layout, current_value)
        if config_type is list:
            return self._build_list_field(layout, config_name, current_value)
        if isinstance(config_setting, ChooseType):
            selection = config_setting.allowed
            return self._build_selection_filed(layout, current_value, selection)
        if isinstance(config_setting, DictType):
            return self._build_dict_field(layout, config_name, current_value)
        return self._build_fallback_field(layout, current_value)

    def _build_int_field(self, layout: QBoxLayout, config_name: str, current_value: int) -> Callable[[], int]:
        """Build a field for integer input with numpad."""
        config_input = ClickableLineEdit(str(current_value))
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        config_input.clicked.connect(lambda: NumpadWidget(self, config_input, 300, 20, config_name))  # type: ignore
        layout.addWidget(config_input)
        return lambda: int(config_input.text() or 0)

    def _build_float_field(self, layout: QBoxLayout, config_name: str, current_value: int) -> Callable[[], float]:
        """Build a field for integer input with numpad."""
        config_input = ClickableLineEdit(str(current_value))
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        config_input.clicked.connect(
            lambda: NumpadWidget(  # type: ignore
                self, config_input, 300, 20, config_name, True
            )
        )
        layout.addWidget(config_input)
        return lambda: float(config_input.text() or 0.0)

    def _build_bool_field(self, layout: QBoxLayout, current_value: bool, displayed_text="on") -> Callable[[], bool]:
        """Build a field for bool input with a checkbox."""
        config_input = QCheckBox(displayed_text)
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        config_input.setChecked(bool(current_value))
        layout.addWidget(config_input)
        return config_input.isChecked

    def _build_list_field(self, layout: QBoxLayout, config_name: str, current_value: list) -> Callable[[], list[Any]]:
        """Build a list of fields for a list input."""
        config_input = QVBoxLayout()
        getter_fn_list: list[Callable] = []
        # iterate over each list value and build the according field
        for initial_value in current_value:
            self._add_ui_element_to_list(initial_value, getter_fn_list, config_name, config_input)
        # adds a button for adding new list entries
        add_button = QPushButton("+ add")
        adjust_font(add_button, MEDIUM_FONT, True)
        add_button.clicked.connect(  # type: ignore[attr-defined]
            lambda: self._add_ui_element_to_list("", getter_fn_list, config_name, config_input)
        )
        # build container that new added elements are above add button separately
        v_container = QVBoxLayout()
        v_container.addLayout(config_input)
        v_container.addWidget(add_button)
        layout.addLayout(v_container)
        return lambda: [x() for x in getter_fn_list]

    def _add_ui_element_to_list(self, initial_value, getter_fn_list: list, config_name: str, container: QBoxLayout):
        """Add an additional input element for list buildup."""
        # Gets the type of the list elements
        config_setting = cfg.config_type.get(config_name)
        # shouldn't happen, but typing is not happy else
        if config_setting is None or not isinstance(config_setting, ListType):
            raise RuntimeError(
                f"Config '{config_name}' is not a list type. That should not happen. Please report the error."
            )
        list_setting = config_setting.list_type
        h_container = QHBoxLayout()
        # need to get the current length of the layout, to get the indicator number
        current_position = container.count() + 1
        position_number = QLabel(str(current_position))
        position_number.setMinimumWidth(18)
        position_number.setMaximumWidth(18)
        h_container.addWidget(position_number)
        getter_fn = self._build_input_field(config_name, list_setting, initial_value, h_container)
        remove_button = QPushButton("x")
        remove_button.setMaximumWidth(30)
        adjust_font(remove_button, MEDIUM_FONT, True)
        # the first argument in lambda is needed since the object reference within the loop
        remove_button.clicked.connect(  # type: ignore[attr-defined]
            lambda _, x=h_container: self._remove_ui_element_from_list(x, getter_fn, getter_fn_list)
        )
        h_container.addWidget(remove_button)
        container.addLayout(h_container)
        getter_fn_list.append(getter_fn)

    def _remove_ui_element_from_list(self, element, getter_fn, getter_fn_list: list[Callable]):
        """Remove the referenced element from the ui."""
        for i in reversed(range(element.count())):
            found_widget = element.itemAt(i).widget()
            found_widget.setParent(None)
        getter_fn_list.remove(getter_fn)
        element.deleteLater()

    def _build_dict_field(self, layout: QBoxLayout, config_name: str, current_value: ConfigClass) -> Callable[[], dict]:
        """Build a dict of fields for a dict input."""
        h_container = QHBoxLayout()
        getter_fn_dict: dict[str, Callable] = {}

        config_setting = cfg.config_type.get(config_name)
        # shouldn't happen, but typing is not happy else
        if config_setting is None or not isinstance(config_setting, DictType):
            raise RuntimeError(
                f"Config '{config_name}' is not a dict type. That should not happen. Please report the error."
            )
        dict_values = current_value.to_config()
        for key, value in dict_values.items():
            value_setting = config_setting.dict_types.get(key)
            if value_setting is None:
                raise RuntimeError(f"Config '{config_name}' has a key '{key}' that is not defined in the dict types.")
            getter_fn = self._build_input_field(config_name, value_setting, value, h_container)
            getter_fn_dict[key] = getter_fn
        layout.addLayout(h_container)
        return lambda: {key: getter() for key, getter in getter_fn_dict.items()}

    def _build_fallback_field(self, layout: QBoxLayout, current_value) -> Callable[[], str]:
        """Build the default input field for string input."""
        config_input = ClickableLineEdit(str(current_value))
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        config_input.clicked.connect(lambda: KeyboardWidget(self, config_input, 200))  # type: ignore
        layout.addWidget(config_input)
        return config_input.text

    def _build_selection_filed(
        self, layout: QBoxLayout, current_value: bool, selection: list[str]
    ) -> Callable[[], str]:
        """Build a field for selection of values with a dropdown / combobox."""
        config_input = QComboBox()
        config_input.addItems(selection)
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        index = config_input.findText(current_value, Qt.MatchFixedString)  # type: ignore
        config_input.setCurrentIndex(index)
        layout.addWidget(config_input)
        return config_input.currentText

    def _retrieve_values(self):
        return {key: getter() for key, getter in self.config_objects.items()}

    def _choose_tab_container(self, config_name: str):
        """Get the object name of the tab container, that the config belongs to."""
        # specific sorting for some values where prefix may not match the category good enough
        exact_sorting = {
            self.vbox_ui: ("MAKER_THEME",),
            self.vbox_hardware: (
                "MAKER_PUMP_REVERSION",
                "MAKER_REVERSION_PIN",
                "MAKER_PINS_INVERTED",
                "MAKER_BOARD",
            ),
        }
        for key, value in exact_sorting.items():
            if config_name in value:
                return key

        # generic sorting dependent on the config prefix
        tab_config = {
            self.vbox_ui: ("UI",),
            self.vbox_maker: ("MAKER",),
            self.vbox_hardware: (
                "PUMP",
                "LED",
                "RFID",
            ),
            self.vbox_software: (
                "MICROSERVICE",
                "TEAM",
            ),
        }
        # go over each key, if one of the values in the list is part of the config name
        # return the key
        for key, value in tab_config.items():
            if any(config_name.lower().startswith(x.lower()) for x in value):
                return key
        # if nothing matches, put it in the other tab
        return self.vbox_other
