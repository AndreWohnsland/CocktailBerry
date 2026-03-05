from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from src.config.config_manager import shared
from src.database_commander import DatabaseCommander, ElementAlreadyExistsError, ElementNotFoundError
from src.db_models import DbWaiterLog
from src.dialog_handler import UI_LANGUAGE
from src.display_controller import DP_CONTROLLER
from src.ui.creation_utils import MEDIUM_FONT, FontSize, adjust_font, create_button, create_label, create_spacer
from src.ui.setup_keyboard_widget import KeyboardWidget
from src.ui_elements import Ui_WaiterWindow
from src.ui_elements.clickablelineedit import ClickableLineEdit

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen


class WaiterWindow(QMainWindow, Ui_WaiterWindow):
    """Creates the waiter window Widget."""

    _PERMISSION_KEYS = ("maker", "ingredients", "recipes", "bottles")

    def __init__(self, mainscreen: MainScreen) -> None:
        """Init. Connect all the buttons and set window policy."""
        super().__init__()
        self.setupUi(self)
        self.mainscreen = mainscreen
        DP_CONTROLLER.initialize_window_object(self)
        self.button_back.clicked.connect(self.close)
        self.waiter_tabs.currentChanged.connect(self._on_tab_changed)

        self._last_seen_nfc_id: str | None = None
        self._editing_nfc_id: str | None = None

        UI_LANGUAGE.adjust_waiter_window(self)
        self._render_management()
        self._render_statistics()

        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._refresh_scan_state)
        self._scan_timer.start(300)
        self._refresh_scan_state()

        self.showFullScreen()
        DP_CONTROLLER.set_display_settings(self)

    def closeEvent(self, a0: Any) -> None:
        if hasattr(self, "_scan_timer"):
            self._scan_timer.stop()
        super().closeEvent(a0)

    def _on_tab_changed(self) -> None:
        if self.waiter_tabs.currentWidget() == self.tab_statistics:
            self._render_statistics()

    def _render_management(self) -> None:
        DP_CONTROLLER.delete_items_of_layout(self.data_container_management)

        self._add_section_header(
            self.data_container_management, UI_LANGUAGE.get_translation("last_scanned", "waiter_window")
        )
        self._scan_id_label = create_label("", FontSize.MEDIUM)
        self._scan_name_label = create_label("", FontSize.MEDIUM)
        self.data_container_management.addWidget(self._scan_id_label)
        self.data_container_management.addWidget(self._scan_name_label)
        self.data_container_management.addItem(create_spacer(10))

        use_scanned_btn = create_button(
            UI_LANGUAGE.get_translation("use_scanned", "waiter_window"),
            font_size=MEDIUM_FONT,
            min_h=50,
            css_class="btn-inverted",
        )
        use_scanned_btn.clicked.connect(self._use_scanned_nfc)
        self.data_container_management.addWidget(use_scanned_btn)

        self.data_container_management.addItem(create_spacer(10))
        self._add_section_header(
            self.data_container_management,
            UI_LANGUAGE.get_translation("register_waiter", "waiter_window"),
        )

        self._create_nfc_input = ClickableLineEdit()
        self._create_nfc_input.setPlaceholderText(UI_LANGUAGE.get_translation("nfc_id_placeholder", "waiter_window"))
        self._create_nfc_input.clicked.connect(self._open_create_nfc_keyboard)
        adjust_font(self._create_nfc_input, MEDIUM_FONT)
        self.data_container_management.addWidget(self._create_nfc_input)

        self._create_name_input = ClickableLineEdit()
        self._create_name_input.setPlaceholderText(UI_LANGUAGE.get_translation("name_placeholder", "waiter_window"))
        self._create_name_input.clicked.connect(self._open_create_name_keyboard)
        adjust_font(self._create_name_input, MEDIUM_FONT)
        self.data_container_management.addWidget(self._create_name_input)

        self.data_container_management.addWidget(
            create_label(UI_LANGUAGE.get_translation("permissions_label", "waiter_window"), FontSize.MEDIUM, min_h=30)
        )
        create_permissions_layout = QHBoxLayout()
        self._create_permission_boxes = self._build_permission_checkboxes(create_permissions_layout, default_maker=True)
        self.data_container_management.addLayout(create_permissions_layout)

        create_btn = create_button(
            UI_LANGUAGE.get_translation("create_waiter", "waiter_window"),
            font_size=MEDIUM_FONT,
            min_h=50,
            css_class="btn-inverted",
        )
        create_btn.clicked.connect(self._create_waiter)
        self.data_container_management.addItem(create_spacer(10))
        self.data_container_management.addWidget(create_btn)

        self._edit_section_widget = QWidget(self.scrollAreaWidgetContents_3)
        self._edit_section_widget.setVisible(False)
        self._render_edit_section()

        self.data_container_management.addItem(create_spacer(10))
        self._add_section_header(
            self.data_container_management,
            UI_LANGUAGE.get_translation("registered_waiters", "waiter_window"),
        )
        self._waiter_list_layout = QVBoxLayout()
        self.data_container_management.addLayout(self._waiter_list_layout)
        self.data_container_management.addItem(create_spacer(1, expand=True))

        self._refresh_waiters_list()

    def _render_edit_section(self) -> None:
        layout = QVBoxLayout(self._edit_section_widget)

        self._edit_name_input = ClickableLineEdit()
        self._edit_name_input.setPlaceholderText(UI_LANGUAGE.get_translation("name_placeholder", "waiter_window"))
        self._edit_name_input.clicked.connect(self._open_edit_name_keyboard)
        adjust_font(self._edit_name_input, MEDIUM_FONT)
        layout.addWidget(self._edit_name_input)

        layout.addWidget(
            create_label(
                UI_LANGUAGE.get_translation("permissions_label", "waiter_window"),
                FontSize.MEDIUM,
                min_h=30,
            )
        )
        permission_layout = QHBoxLayout()
        self._edit_permission_boxes = self._build_permission_checkboxes(permission_layout, default_maker=True)
        layout.addLayout(permission_layout)
        layout.addItem(create_spacer(10))

        actions = QHBoxLayout()
        save_btn = create_button(
            UI_LANGUAGE.get_translation("save", "waiter_window"),
            font_size=MEDIUM_FONT,
            min_h=45,
            css_class="btn-inverted",
        )
        save_btn.clicked.connect(self._save_waiter)
        cancel_btn = create_button(
            UI_LANGUAGE.get_translation("cancel", "waiter_window"),
            font_size=MEDIUM_FONT,
            min_h=45,
        )
        cancel_btn.clicked.connect(self._cancel_edit)
        actions.addWidget(save_btn)
        actions.addWidget(cancel_btn)
        layout.addLayout(actions)

    def _build_permission_checkboxes(self, layout: QHBoxLayout, default_maker: bool) -> dict[str, QCheckBox]:
        boxes: dict[str, QCheckBox] = {}
        for key in self._PERMISSION_KEYS:
            checkbox = QCheckBox(UI_LANGUAGE.get_translation(f"permission_{key}", "waiter_window"))
            adjust_font(checkbox, MEDIUM_FONT)
            checkbox.setChecked(default_maker and key == "maker")
            boxes[key] = checkbox
            layout.addWidget(checkbox)
        return boxes

    def _refresh_scan_state(self) -> None:
        current_nfc_id = shared.current_waiter_nfc_id
        current_name = (
            shared.current_waiter.name
            if shared.current_waiter is not None
            else UI_LANGUAGE.get_translation("no_waiter", "waiter_window")
        )
        self._scan_id_label.setText(
            f"{UI_LANGUAGE.get_translation('current_nfc', 'waiter_window')}: {current_nfc_id or '-'}"
        )
        current_waiter_label = UI_LANGUAGE.get_translation("current_waiter", "waiter_window")
        self._scan_name_label.setText(f"{current_waiter_label}: {current_name}")

        if current_nfc_id != self._last_seen_nfc_id:
            self._last_seen_nfc_id = current_nfc_id
            self._refresh_waiters_list()

    def _use_scanned_nfc(self) -> None:
        if shared.current_waiter_nfc_id is not None:
            self._create_nfc_input.setText(shared.current_waiter_nfc_id)

    def _create_waiter(self) -> None:
        nfc_id = self._create_nfc_input.text().strip()
        name = self._create_name_input.text().strip()
        if not nfc_id or not name:
            DP_CONTROLLER.say_some_value_missing()
            return
        permissions = self._collect_permissions(self._create_permission_boxes)
        try:
            DatabaseCommander().create_waiter(nfc_id=nfc_id, name=name, permissions=permissions)
        except ElementAlreadyExistsError:
            DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_exists", "waiter_window"))
            return

        self._create_nfc_input.clear()
        self._create_name_input.clear()
        for key, checkbox in self._create_permission_boxes.items():
            checkbox.setChecked(key == "maker")

        DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_created", "waiter_window"), close_time=5)
        self._refresh_waiters_list()

    def _start_edit_waiter(self, nfc_id: str) -> None:
        waiter = DatabaseCommander().get_waiter_by_nfc_id(nfc_id)
        if waiter is None:
            return
        self._editing_nfc_id = nfc_id
        self._edit_name_input.setText(waiter.name)
        self._edit_permission_boxes["maker"].setChecked(waiter.privilege_maker)
        self._edit_permission_boxes["ingredients"].setChecked(waiter.privilege_ingredients)
        self._edit_permission_boxes["recipes"].setChecked(waiter.privilege_recipes)
        self._edit_permission_boxes["bottles"].setChecked(waiter.privilege_bottles)
        self._refresh_waiters_list()

    def _save_waiter(self) -> None:
        if self._editing_nfc_id is None:
            return
        edit_name = self._edit_name_input.text().strip()
        if not edit_name:
            DP_CONTROLLER.say_some_value_missing()
            return
        permissions = self._collect_permissions(self._edit_permission_boxes)
        try:
            DatabaseCommander().update_waiter(self._editing_nfc_id, name=edit_name, permissions=permissions)
        except ElementAlreadyExistsError:
            DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_exists", "waiter_window"))
            return
        except ElementNotFoundError:
            DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_not_found", "waiter_window"))
            self._cancel_edit()
            return
        DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_updated", "waiter_window"), close_time=5)
        self._cancel_edit()
        self._refresh_waiters_list()

    def _cancel_edit(self) -> None:
        self._editing_nfc_id = None
        self._edit_section_widget.setVisible(False)
        self._refresh_waiters_list()

    def _delete_waiter(self, nfc_id: str, waiter_name: str) -> None:
        if not DP_CONTROLLER.ask_to_delete_x(waiter_name):
            return
        try:
            DatabaseCommander().delete_waiter(nfc_id)
        except ElementNotFoundError:
            DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_not_found", "waiter_window"))
            return
        DP_CONTROLLER.standard_box(UI_LANGUAGE.get_translation("waiter_deleted", "waiter_window"), close_time=5)
        if self._editing_nfc_id == nfc_id:
            self._cancel_edit()
        self._refresh_waiters_list()
        self._render_statistics()

    def _refresh_waiters_list(self) -> None:
        self._edit_section_widget.setVisible(False)
        DP_CONTROLLER.delete_items_of_layout(self._waiter_list_layout)

        waiters = DatabaseCommander().get_all_waiters()
        if not waiters:
            self._waiter_list_layout.addWidget(
                create_label(UI_LANGUAGE.get_translation("no_waiters", "waiter_window"), FontSize.MEDIUM, centered=True)
            )
            return

        for waiter in waiters:
            if self._editing_nfc_id == waiter.nfc_id:
                self._waiter_list_layout.addWidget(self._edit_section_widget)
                self._edit_section_widget.setVisible(True)
                self._waiter_list_layout.addItem(create_spacer(10))

            card = QWidget()
            card_layout = QVBoxLayout(card)
            active_suffix = (
                f" ({UI_LANGUAGE.get_translation('active', 'waiter_window')})"
                if shared.current_waiter_nfc_id == waiter.nfc_id
                else ""
            )
            card_layout.addWidget(create_label(f"{waiter.name}{active_suffix}", FontSize.MEDIUM, bold=True))
            card_layout.addWidget(create_label(waiter.nfc_id, FontSize.SMALL))

            permission_names = [
                UI_LANGUAGE.get_translation(f"permission_{key}", "waiter_window")
                for key in self._PERMISSION_KEYS
                if bool(getattr(waiter, f"privilege_{key}"))
            ]
            if permission_names:
                card_layout.addWidget(create_label(", ".join(permission_names), FontSize.SMALL, css_class="secondary"))
            card_layout.addItem(create_spacer(4))

            action_layout = QHBoxLayout()
            edit_btn = create_button(
                UI_LANGUAGE.get_translation("edit", "waiter_window"),
                font_size=MEDIUM_FONT,
                min_h=45,
                css_class="btn-inverted",
            )
            edit_btn.clicked.connect(lambda _, nfc=waiter.nfc_id: self._start_edit_waiter(nfc))
            delete_btn = create_button(
                UI_LANGUAGE.get_translation("delete", "waiter_window"),
                font_size=MEDIUM_FONT,
                min_h=45,
                css_class="destructive",
            )
            delete_btn.clicked.connect(lambda _, nfc=waiter.nfc_id, name=waiter.name: self._delete_waiter(nfc, name))
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            card_layout.addLayout(action_layout)
            self._waiter_list_layout.addWidget(card)

    def _render_statistics(self) -> None:
        DP_CONTROLLER.delete_items_of_layout(self.data_container_statistics)
        logs = DatabaseCommander().get_waiter_logs()
        if not logs:
            self.data_container_statistics.addWidget(
                create_label(UI_LANGUAGE.get_translation("no_logs", "waiter_window"), FontSize.MEDIUM, centered=True)
            )
            self.data_container_statistics.addItem(create_spacer(1, expand=True))
            return

        grouped: dict[str, dict[str, list[DbWaiterLog]]] = defaultdict(lambda: defaultdict(list))
        for log in logs:
            date_key = log.timestamp.strftime("%Y-%m-%d")
            waiter_name = (
                log.waiter.name
                if log.waiter is not None
                else UI_LANGUAGE.get_translation("deleted_user", "waiter_window")
            )
            grouped[date_key][waiter_name].append(log)

        for date_key, waiters in grouped.items():
            date_logs = [entry for waiter_logs in waiters.values() for entry in waiter_logs]
            date_summary = self._build_stats_summary(len(date_logs), sum(log.volume for log in date_logs))
            self._add_section_header(self.data_container_statistics, f"{date_key} - {date_summary}")
            for waiter_name, waiter_logs in waiters.items():
                self.data_container_statistics.addWidget(self._build_waiter_log_group(waiter_name, waiter_logs))

        self.data_container_statistics.addItem(create_spacer(1, expand=True))

    def _build_waiter_log_group(self, waiter_name: str, logs: list[DbWaiterLog]) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(4)
        summary = self._build_stats_summary(len(logs), sum(log.volume for log in logs))
        toggle = create_button(
            f"{waiter_name} ({summary})",
            font_size=MEDIUM_FONT,
            min_h=45,
            css_class="btn-inverted",
        )
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content.setVisible(False)

        for log in logs:
            time_str = log.timestamp.strftime("%H:%M")
            recipe_name = (
                log.recipe.name
                if log.recipe is not None
                else UI_LANGUAGE.get_translation("deleted_recipe", "waiter_window")
            )
            virgin_suffix = f" ({UI_LANGUAGE.get_translation('virgin', 'waiter_window')})" if log.is_virgin else ""
            content_layout.addWidget(
                create_label(
                    f"{time_str} - {recipe_name} - {log.volume} ml{virgin_suffix}",
                    FontSize.SMALL,
                )
            )

        toggle.clicked.connect(lambda: content.setVisible(not content.isVisible()))
        wrapper_layout.addWidget(toggle)
        wrapper_layout.addWidget(content)
        return wrapper

    def _collect_permissions(self, checkboxes: dict[str, QCheckBox]) -> dict[str, bool]:
        return {key: box.isChecked() for key, box in checkboxes.items()}

    def _build_stats_summary(self, cocktails_count: int, total_volume_ml: int) -> str:
        return UI_LANGUAGE.get_translation(
            "stats_summary",
            "waiter_window",
            cocktails=cocktails_count,
            volume=total_volume_ml,
        )

    def _add_section_header(self, layout: QVBoxLayout, text: str) -> None:
        layout.addWidget(create_label(text, FontSize.LARGE, bold=True, min_h=36, css_class="secondary"))
        layout.addItem(create_spacer(6))

    def _open_create_nfc_keyboard(self) -> None:
        KeyboardWidget(self.mainscreen, self._create_nfc_input)

    def _open_create_name_keyboard(self) -> None:
        KeyboardWidget(self.mainscreen, self._create_name_input)

    def _open_edit_name_keyboard(self) -> None:
        KeyboardWidget(self.mainscreen, self._edit_name_input)
