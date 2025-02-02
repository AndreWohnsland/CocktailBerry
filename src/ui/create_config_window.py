from __future__ import annotations

from typing import Any, Callable, Literal, Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
)

from src.config.config_manager import CONFIG as cfg
from src.config.config_types import (
    BoolType,
    ChooseType,
    ConfigClass,
    ConfigInterface,
    DictType,
    FloatType,
    IntType,
    ListType,
)
from src.config.errors import ConfigError
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui.creation_utils import (
    LARGE_FONT,
    MEDIUM_FONT,
    SMALL_FONT,
    adjust_font,
    create_button,
    create_label,
    create_spacer,
)
from src.ui.setup_color_window import ColorWindow
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui.setup_numpad_widget import NumpadWidget
from src.ui_elements import Ui_ConfigWindow
from src.ui_elements.clickablelineedit import ClickableLineEdit
from src.utils import restart_program

CONFIG_TYPES_POSSIBLE = Union[str, int, float, bool, list[Any], dict[str, Any]]
# Those are only for the v2 program
CONFIG_TO_SKIP = (
    "CUSTOM_COLOR_PRIMARY",
    "CUSTOM_COLOR_SECONDARY",
    "CUSTOM_COLOR_NEUTRAL",
    "CUSTOM_COLOR_BACKGROUND",
    "CUSTOM_COLOR_DANGER",
    "EXP_DEMO_MODE",
)


class ConfigWindow(QMainWindow, Ui_ConfigWindow):
    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        DP_CONTROLLER.initialize_window_object(self)
        self.mainscreen = parent
        self.config_objects = {}
        self.color_window: ColorWindow | None = None
        self.button_custom_color: QPushButton | None = None
        UI_LANGUAGE.adjust_config_window(self)
        self._init_ui()
        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def _init_ui(self):
        # adds all the configs to the window
        for key, config_setting in cfg.config_type.items():
            if key in CONFIG_TO_SKIP:
                continue
            self._choose_display_style(key, config_setting)

        self.button_save.clicked.connect(self._save_config)
        self.button_back.clicked.connect(self.close)
        # other window may have little elements and spacing is bad,
        # so add a spacer to the end
        self.vbox_other.addItem(create_spacer(1, expand=True))

    def _save_config(self):
        try:
            cfg.set_config(self._retrieve_values(), True)
            cfg.sync_config_to_file()
        except ConfigError as err:
            DP_CONTROLLER.say_wrong_config(str(err))
            return
        # Also asks if to restart program to get new config
        if DP_CONTROLLER.ask_to_restart_for_config():
            restart_program(is_v1=True)
        self.close()

    def _choose_display_style(self, config_name: str, config_setting: ConfigInterface):
        """Create the input face for the according config types."""
        # Add the elements header to the view
        header = create_label(f"{config_name}:", font_size=LARGE_FONT, bold=True)
        vbox = self._choose_tab_container(config_name)
        vbox.addWidget(header)
        description_text = UI_LANGUAGE.get_config_description(config_name)
        if description_text:
            description = create_label(description_text, font_size=SMALL_FONT)
            description.setWordWrap(True)
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
        self.button_custom_color = create_button(
            "Define Custom Color", min_w=0, max_w=16777215, max_h=200, min_h=50, font_size=LARGE_FONT, bold=True
        )
        self.button_custom_color.clicked.connect(self._open_color_window)  # type: ignore
        vbox.addWidget(self.button_custom_color)  # type: ignore[arg-type]

    def _open_color_window(self):
        self.color_window = ColorWindow(self.mainscreen)

    def _build_input_field(
        self, config_name: str, config_setting: ConfigInterface, current_value: Any, layout: QBoxLayout | None = None
    ) -> Callable[[], CONFIG_TYPES_POSSIBLE]:
        """Build the input field and returns its getter function."""
        if layout is None:
            # get the tab container and build a horizontal layout for the config
            # this is needed in case we want to add pre- or suffixes, which are otherwise not in the same line
            container = self._choose_tab_container(config_name)
            layout = QHBoxLayout()
            container.addLayout(layout)

        if config_setting.prefix is not None:
            prefix_text = create_label(f" {config_setting.prefix}", MEDIUM_FONT)
            layout.addWidget(prefix_text)

        if isinstance(config_setting, IntType):
            field: Callable[[], CONFIG_TYPES_POSSIBLE] = self._build_int_field(layout, config_name, current_value)
        elif isinstance(config_setting, FloatType):
            field = self._build_float_field(layout, config_name, current_value)
        elif isinstance(config_setting, BoolType):
            field = self._build_bool_field(layout, current_value, config_setting.check_name)
        elif isinstance(config_setting, ListType):
            field = self._build_list_field(layout, config_name, current_value, config_setting)
        elif isinstance(config_setting, ChooseType):
            field = self._build_selection_filed(layout, current_value, config_setting.allowed)
        elif isinstance(config_setting, DictType):
            field = self._build_dict_field(layout, config_name, current_value, config_setting)
        else:
            field = self._build_fallback_field(layout, current_value)

        if config_setting.suffix is not None:
            suffix_text = create_label(f"{config_setting.suffix} ", MEDIUM_FONT)
            layout.addWidget(suffix_text)
        return field

    def _build_int_field(self, layout: QBoxLayout, config_name: str, current_value: int) -> Callable[[], int]:
        """Build a field for integer input with numpad."""
        config_input = ClickableLineEdit(str(current_value))
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        config_input.clicked.connect(
            lambda: NumpadWidget(  # type: ignore
                self, config_input, 300, 20, config_name, header_is_entered_number=True
            )
        )
        layout.addWidget(config_input)
        return lambda: int(config_input.text() or 0)

    def _build_float_field(self, layout: QBoxLayout, config_name: str, current_value: int) -> Callable[[], float]:
        """Build a field for integer input with numpad."""
        config_input = ClickableLineEdit(str(current_value))
        adjust_font(config_input, MEDIUM_FONT)
        config_input.setProperty("cssClass", "secondary")
        config_input.clicked.connect(
            lambda: NumpadWidget(  # type: ignore
                self, config_input, 300, 20, config_name, True, header_is_entered_number=True
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

    def _build_list_field(
        self, layout: QBoxLayout, config_name: str, current_value: list, config_setting: ListType
    ) -> Callable[[], list[Any]]:
        """Build a list of fields for a list input."""
        config_input = QVBoxLayout()
        getter_fn_list: list[Callable] = []
        # in case there was an alteration of the config file, immutable lists may have less elements
        # than they should have, so we need to add empty strings to the list
        if config_setting.immutable:
            min_length = (
                config_setting.min_length if isinstance(config_setting.min_length, int) else config_setting.min_length()
            )
            current_value += [""] * max(0, (min_length - len(current_value)))
            # also cut off the list in case there are too many elements
            current_value = current_value[:min_length]
        # iterate over each list value and build the according field
        for initial_value in current_value:
            self._add_ui_element_to_list(initial_value, getter_fn_list, config_name, config_input, config_setting)
        # build container that new added elements are above add button separately
        v_container = QVBoxLayout()
        v_container.addLayout(config_input)
        # adds a button for adding new list entries if it is not immutable
        if not config_setting.immutable:
            add_button = create_button("+ add", font_size=MEDIUM_FONT, min_h=0, bold=True, css_class="neutral")
            add_button.clicked.connect(  # type: ignore[attr-defined]
                lambda: self._add_ui_element_to_list("", getter_fn_list, config_name, config_input, config_setting)
            )

            v_container.addWidget(add_button)
        layout.addLayout(v_container)
        return lambda: [x() for x in getter_fn_list]

    def _add_ui_element_to_list(
        self,
        initial_value,
        getter_fn_list: list,
        config_name: str,
        container: QBoxLayout,
        config_setting: ListType,
    ):
        """Add an additional input element for list buildup."""
        # Gets the type of the list elements
        list_setting = config_setting.list_type
        h_container = QHBoxLayout()
        # need to get the current length of the layout, to get the indicator number
        current_position = container.count() + 1
        position_number = create_label(str(current_position), font_size=10, min_w=18, max_w=18)
        h_container.addWidget(position_number)
        getter_fn = self._build_input_field(config_name, list_setting, initial_value, h_container)
        if not config_setting.immutable:
            remove_button = create_button(
                " x ", font_size=MEDIUM_FONT, max_w=40, min_h=0, bold=True, css_class="destructive"
            )
            # the first argument in lambda is needed since the object reference within the loop
            remove_button.clicked.connect(  # type: ignore[attr-defined]
                lambda _, x=h_container: self._remove_ui_element_from_list(x, getter_fn, getter_fn_list)
            )
            h_container.addWidget(remove_button)
        container.addLayout(h_container)
        getter_fn_list.append(getter_fn)

    def _remove_ui_element_from_list(self, element: QHBoxLayout, getter_fn, getter_fn_list: list[Callable]):
        """Remove the referenced element from the ui."""

        def recursive_delete(widget: QBoxLayout):
            """Recursively delete all children of the given widget."""
            for i in reversed(range(widget.count())):
                found_element = widget.itemAt(i)
                found_widget = found_element.widget()
                if found_widget is not None:
                    found_widget.setParent(None)  # type: ignore
                    found_widget.deleteLater()
                if isinstance(found_element, QBoxLayout):
                    recursive_delete(found_element)

        recursive_delete(element)
        getter_fn_list.remove(getter_fn)
        element.deleteLater()

    def _build_dict_field(
        self,
        layout: QBoxLayout,
        config_name: str,
        current_value: ConfigClass | Literal[""],
        config_setting: DictType,
    ) -> Callable[[], dict]:
        """Build a dict of fields for a dict input."""
        h_container = QHBoxLayout()
        getter_fn_dict: dict[str, Callable] = {}
        # if used with the list constructor, we will get a empty string, if a new value is added to the list.
        # in this case extract the dict keys from the config setting and use empty strings as values
        if current_value == "":
            dict_values = {key: "" for key in config_setting.dict_types}
        else:
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
