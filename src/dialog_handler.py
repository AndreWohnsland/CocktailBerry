# otherwise circular import :(
# pylint: disable=import-outside-toplevel

from __future__ import annotations

import time
from pathlib import Path
from threading import Event, Thread
from typing import TYPE_CHECKING, Literal

import yaml

# We do not need those in v2, so its okay to fail there
try:
    from PyQt5.QtCore import QEventLoop, Qt
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QDialog, QFileDialog
except ModuleNotFoundError:
    pass

from src import __version__
from src.config.config_manager import CONFIG as cfg
from src.filepath import APP_ICON_FILE, LANGUAGE_FILE, STYLE_FOLDER
from src.logger_handler import LoggerHandler
from src.utils import get_platform_data

if TYPE_CHECKING:
    from src.ui_elements import (
        Ui_addingredient,
        Ui_AddonManager,
        Ui_Addonwindow,
        Ui_available,
        Ui_Bottlewindow,
        Ui_CocktailSelection,
        Ui_ColorWindow,
        Ui_ConfigWindow,
        Ui_CustomDialog,
        Ui_CustomPrompt,
        Ui_DataWindow,
        Ui_Datepicker,
        Ui_LogWindow,
        Ui_MainWindow,
        Ui_Optionwindow,
        Ui_PasswordDialog,
        Ui_PictureWindow,
        Ui_Progressbarwindow,
        Ui_RefillPrompt,
        Ui_RFIDWriterWindow,
        Ui_Teamselection,
        Ui_WiFiWindow,
    )

_logger = LoggerHandler("dialog_handler")

allowed_keys = Literal[
    "alcohol_level_max_limit",
    "all_data_exported",
    "all_recipes_enabled",
    "ask_adjust_time",
    "ask_backup_overwrite",
    "ask_enable_all_recipes",
    "ask_export_data",
    "ask_for_backup_location",
    "ask_for_image_location",
    "ask_to_clean",
    "ask_to_delete_x",
    "ask_to_install_qtsass",
    "ask_to_reboot",
    "ask_to_remove_picture",
    "ask_to_shutdown",
    "ask_to_system_update",
    "ask_to_use_reverted_pump",
    "available_ingredient_updated",
    "backup_created",
    "backup_failed",
    "bottle_calibration_started",
    "bottle_tab_locked",
    "bottle_updated",
    "bottles_renewed",
    "box_title",
    "cleaning_started",
    "cocktail_canceled",
    "cocktail_in_progress",
    "cocktail_ready_add",
    "cocktail_ready",
    "cocktailberry_up_to_date",
    "confirmation_required",
    "create_cocktail_first",
    "done",
    "element_already_exists",
    "element_not_found",
    "enter_cocktail_name",
    "hand_ingredient_cannot_prepared",
    "image_deleted",
    "image_processing_failed",
    "image_uploaded",
    "ingredient_added",
    "ingredient_changed",
    "ingredient_deleted",
    "ingredient_double_usage",
    "ingredient_must_be_handadd",
    "ingredient_not_connected",
    "ingredient_still_as_machine_add",
    "ingredient_still_at_bottle",
    "ingredient_still_at_recipe",
    "ingredient_still_in_available",
    "internet_connection_not_ok",
    "internet_connection_ok",
    "name_already_exists",
    "needs_to_be_int_specific",
    "needs_to_be_int",
    "no_button",
    "no_ingredient_selected",
    "no_recipe_selected",
    "not_enough_ingredient_volume",
    "options_updated",
    "options_updated_and_restart",
    "preparation_cancelled",
    "python_deprecated",
    "qtsass_not_successful",
    "recipe_added",
    "recipe_at_least_one_ingredient",
    "recipe_deleted",
    "recipe_help",
    "recipe_updated",
    "restart_config",
    "some_value_missing_specific",
    "some_value_missing",
    "update_available",
    "update_failed",
    "welcome_dialog",
    "wifi_failure",
    "wifi_setup_failed",
    "wifi_success",
    "wrong_config",
    "wrong_password",
    "yes_button",
]


class DialogHandler:
    """Class to hold all the dialogues for the popups and language settings."""

    def __init__(self) -> None:
        self.icon_path = str(APP_ICON_FILE)
        self.password_outcome = False
        self.prompt_outcome = False
        self.message_box: None | Ui_CustomDialog = None
        with open(LANGUAGE_FILE, encoding="UTF-8") as stream:
            self.dialogs: dict[str, dict[str, str]] = yaml.safe_load(stream)["dialog"]

    def get_translation(self, dialog_key: allowed_keys, **kwargs) -> str:
        try:
            return self._choose_language(dialog_key, **kwargs)
        except KeyError:
            _logger.error(f"No translation for {dialog_key} found")
            return "ERROR: NO TRANSLATION FOUND"

    def _choose_language(self, dialog_name: str, **kwargs) -> str:
        """Choose either the given language if exists, or english if not piping additional info into template."""
        language = cfg.UI_LANGUAGE
        element = self.dialogs[dialog_name]
        tmpl = element.get(language, element["en"])
        return tmpl.format(**kwargs)

    def standard_box(self, message: str, title: str = "", use_ok=False, close_time: int | None = None):
        """Display the messagebox for the Maker. Uses a Custom QDialog with Close-Button."""
        from src.ui.setup_custom_dialog import CustomDialog

        def close_thread(event: Event, box: CustomDialog, close_time: int):
            """Close the box after given time if event is not set."""
            time.sleep(close_time)
            if event.is_set():
                return
            box.close()

        if not title:
            title = self._choose_language("box_title")
        fill_string = "-" * 70
        fancy_message = f"{fill_string}\n{message}\n{fill_string}"
        event = Event()
        self.message_box = CustomDialog(fancy_message, title, use_ok, event.set)
        # If there is a close time, start auto close
        if close_time is not None:
            auto_closer = Thread(
                target=close_thread,
                args=(
                    event,
                    self.message_box,
                    close_time,
                ),
                daemon=True,
            )
            auto_closer.start()
        # Need to set event, in case thread is still waiting

    def user_okay(self, text: str):
        """Prompts the user for the given message and asks for confirmation.

        Args:
        ----
            text (str): Text to be displayed

        Returns:
        -------
            bool: If the user accepted the prompted message

        """
        from src.ui.setup_custom_prompt import CustomPrompt

        self.prompt_outcome = False
        loop = QEventLoop()

        def handle_dialog_outcome(result: bool):
            self.prompt_outcome = result
            loop.quit()

        msg_box = CustomPrompt(text)
        msg_box.user_okay.connect(handle_dialog_outcome)

        loop.exec_()

        return self.prompt_outcome

    def password_prompt(
        self,
        right_password: int,
        header_type: Literal["master", "maker"] = "master",
    ):
        """Open a password prompt, return if successful entered password.

        Option to also use other than master password
        This is useful for example for the UI_MAKER_PASSWORD, or if needed for more things in the future.
        """
        from src.ui.setup_password_dialog import PasswordDialog

        # if password is empty, return true
        # Empty means zero in this case, since the config is an int
        if right_password == 0:
            return True
        self.password_outcome = False
        loop = QEventLoop()

        def handle_dialog_outcome(result: bool):
            self.password_outcome = result
            loop.quit()

        password_window = PasswordDialog(right_password, header_type)
        password_window.password_success.connect(handle_dialog_outcome)

        loop.exec_()

        return self.password_outcome

    def __output_language_dialog(self, dialog_name: str, use_ok=False, close_time: int | None = None, **kwargs):
        msg = self._choose_language(dialog_name, **kwargs)
        self.standard_box(msg, use_ok=use_ok, close_time=close_time)

    def _generate_file_dialog(self, message: str = ""):
        """Create the base file dialog and shows it with the full screen settings."""
        file_dialog = QFileDialog()
        style_file = f"{cfg.MAKER_THEME}.css"
        with open(STYLE_FOLDER / style_file, encoding="utf-8") as file_handler:
            file_dialog.setStyleSheet(file_handler.read())
        file_dialog.setWindowIcon(QIcon(self.icon_path))
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # type: ignore
        file_dialog.setWindowTitle(message)
        file_dialog.setWindowFlags(
            Qt.Dialog  # type: ignore
            | Qt.FramelessWindowHint  # type: ignore
            | Qt.CustomizeWindowHint  # type: ignore
            | Qt.WindowStaysOnTopHint  # type: ignore
            | Qt.X11BypassWindowManagerHint  # type: ignore
        )
        if not cfg.UI_DEVENVIRONMENT:
            file_dialog.setCursor(Qt.BlankCursor)  # type: ignore
        file_dialog.setViewMode(QFileDialog.List)  # type: ignore
        file_dialog.showFullScreen()
        file_dialog.setFixedSize(cfg.UI_WIDTH, cfg.UI_HEIGHT)
        file_dialog.resize(cfg.UI_WIDTH, cfg.UI_HEIGHT)
        file_dialog.move(0, 0)
        file_dialog.raise_()
        return file_dialog

    def _parse_file_dialog(self, file_dialog: QFileDialog):
        """Extract the selected file/folder from the file dialog."""
        if file_dialog.exec_() == QDialog.Accepted:  # type: ignore
            file_name = file_dialog.selectedFiles()[0]  # get the selected file
            # Qt will return empty string if user cancels the dialog
            if file_name:
                return Path(file_name).absolute()
        return None

    def _get_folder_location(self, message: str):
        """Return the selected folder."""
        file_dialog = self._generate_file_dialog(message)
        file_dialog.setFileMode(QFileDialog.Directory)  # type: ignore
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)  # type: ignore
        return self._parse_file_dialog(file_dialog)

    def get_file_location(self, message: str, filter_str: str):
        """Return the selected file."""
        file_dialog = self._generate_file_dialog(message)
        file_dialog.setFileMode(QFileDialog.ExistingFile)  # type: ignore
        file_dialog.setNameFilter(filter_str)
        return self._parse_file_dialog(file_dialog)

    ############################
    # Methods for creating msg #
    ############################

    def say_wrong_password(self):
        """Informs user that the password is wrong."""
        self.__output_language_dialog("wrong_password")

    def say_done(self):
        """Informs user that process is done."""
        self.__output_language_dialog("done")

    def say_bottles_renewed(self):
        """Informs user that the bottles have been renewed."""
        self.__output_language_dialog("bottles_renewed")

    def say_no_recipe_selected(self):
        """Informs user that no recipe is selected."""
        self.__output_language_dialog("no_recipe_selected")

    def say_no_ingredient_selected(self):
        """Informs user that no ingredient is selected."""
        self.__output_language_dialog("no_ingredient_selected")

    def say_ingredient_still_at_bottle(self):
        """Informs user that the ingredient is still used at a bottle."""
        self.__output_language_dialog("ingredient_still_at_bottle")

    def say_ingredient_still_at_recipe(self, recipe_string: str):
        """Informs user that the ingredient is still used in a recipe."""
        self.__output_language_dialog("ingredient_still_at_recipe", recipe_string=recipe_string)

    def say_ingredient_still_as_machine_in_recipe(self, recipe_list: list[str]):
        """Informs user that the ingredient is still used in a recipe as machine add."""
        formatted_string = ", ".join(recipe_list)
        self.__output_language_dialog("ingredient_still_as_machine_add", recipe_list=formatted_string)

    def say_ingredient_double_usage(self, ingredient_name: str):
        """Informs user that the ingredient is already used at least one other time."""
        self.__output_language_dialog("ingredient_double_usage", ingredient_name=ingredient_name)

    def say_ingredient_deleted(self, ingredient_name: str):
        """Informs user that the ingredient was deleted."""
        self.__output_language_dialog("ingredient_deleted", ingredient_name=ingredient_name)

    def __say_ingredient_added(self, ingredient_name: str):
        """Informs user that the ingredient was added to the database."""
        self.__output_language_dialog("ingredient_added", ingredient_name=ingredient_name)

    def __say_ingredient_changed(self, selected_ingredient: str | None, ingredient_name: str):
        """Informs user that the ingredient was changed."""
        self.__output_language_dialog(
            "ingredient_changed", selected_ingredient=selected_ingredient, ingredient_name=ingredient_name
        )

    def say_ingredient_added_or_changed(
        self, ingredient_name: str, new_ingredient: bool, selected_ingredient: str | None = None
    ):
        """Informs user that the ingredient was added or altered."""
        if new_ingredient:
            self.__say_ingredient_added(ingredient_name)
        else:
            self.__say_ingredient_changed(selected_ingredient, ingredient_name)

    def say_cocktail_canceled(self):
        """Informs user that the cocktail was canceled."""
        self.__output_language_dialog("cocktail_canceled", close_time=10)

    def cocktail_ready(self, comment: str) -> str:
        """Cocktail is done with additional information what to add."""
        # no more message if there is no additional information
        if len(comment) == 0:
            return ""
        header_comment = self._choose_language("cocktail_ready_add")
        full_comment = f"\n\n{header_comment}{comment}"
        return self._choose_language("cocktail_ready", full_comment=full_comment)

    def say_cocktail_ready(self, comment: str):
        """Informs user that the cocktail is done with additional information what to add."""
        # no more message if there is no additional information
        if not comment:
            return
        close_time = 60
        msg = self.cocktail_ready(comment)
        self.standard_box(msg, close_time=close_time)

    def say_enter_cocktail_name(self):
        """Informs user that no cocktail name was supplied."""
        self.__output_language_dialog("enter_cocktail_name")

    def say_recipe_deleted(self, recipe_name: str):
        """Informs user that the recipe was deleted."""
        self.__output_language_dialog("recipe_deleted", recipe_name=recipe_name)

    def say_all_recipes_enabled(self):
        """Informs user that all recipes have been enabled."""
        self.__output_language_dialog("all_recipes_enabled")

    def say_recipe_added(self, recipe_name: str):
        """Informs user that the recipe was added to the database."""
        self.__output_language_dialog("recipe_added", recipe_name=recipe_name)

    def say_recipe_updated(self, old_name: str, new_name: str):
        """Informs user that the recipe was updated."""
        self.__output_language_dialog("recipe_updated", old_name=old_name, new_name=new_name)

    def say_recipe_at_least_one_ingredient(self):
        """Informs user that the recipe got no according ingredients."""
        self.__output_language_dialog("recipe_at_least_one_ingredient")

    def say_all_data_exported(self, file_path: str):
        """Informs user that all data have been exported."""
        self.__output_language_dialog("all_data_exported", file_path=file_path)

    def not_enough_ingredient_volume(self, ingredient_name: str, level: int, volume: int):
        """Informs user that the ingredient got not enough volume for cocktail."""
        level = max(0, level)
        volume = max(0, volume)
        return self._choose_language(
            "not_enough_ingredient_volume", ingredient_name=ingredient_name, volume=volume, level=level
        )

    def say_not_enough_ingredient_volume(self, ingredient_name: str, level: int, volume: int):
        """Informs user that the ingredient got not enough volume for cocktail."""
        level = max(0, level)
        volume = max(0, volume)
        msg = self.not_enough_ingredient_volume(ingredient_name, level, volume)
        self.standard_box(msg)

    def cocktail_in_progress(self):
        return self._choose_language("cocktail_in_progress")

    def say_name_already_exists(self):
        """Informs user that there is already an entry in the DB with that name."""
        self.__output_language_dialog("name_already_exists")

    def say_some_value_missing(self, value: str | None = None):
        """Informs user that he missed at least one value."""
        if value is None:
            self.__output_language_dialog("some_value_missing")
        else:
            self.__output_language_dialog("some_value_missing_specific", value=value)

    def say_needs_to_be_int(self, value: str | None = None):
        """Informs user that the given value is not a number."""
        if value is None:
            self.__output_language_dialog("needs_to_be_int")
        else:
            self.__output_language_dialog("needs_to_be_int_specific", value=value)

    def say_alcohol_level_max_limit(self):
        """Informs user that the alcohol level can not be greater than 100."""
        self.__output_language_dialog("alcohol_level_max_limit")

    def say_wrong_config(self, error: str):
        """Informs the user that the config is wrong with the error message."""
        self.__output_language_dialog("wrong_config", error=error)

    def say_backup_created(self, folder: str):
        """Informs the user that the backup has been created."""
        self.__output_language_dialog("backup_created", folder=folder)

    def say_backup_failed(self, file: str):
        """Informs the user that the backup has failed."""
        self.__output_language_dialog("backup_failed", file=file)

    def say_python_deprecated(self, sys_python: str, program_python: str):
        """Inform that the given system python is older than the recommended python for the program."""
        self.__output_language_dialog("python_deprecated", sys_python=sys_python, program_python=program_python)

    def say_welcome_message(self):
        """Display the welcome dialog, show version and platform info."""
        self.__output_language_dialog("welcome_dialog", version=__version__, platform=get_platform_data())

    def say_wifi_entered(self, success: bool, ssid: str, password: str):
        """Informs the user about the wifi enter process."""
        if success:
            self.__output_language_dialog("wifi_success")
            return
        self.__output_language_dialog(
            "wifi_failure",
            ssid=ssid,
            password=password,
        )

    def say_wifi_setup_failed(self):
        """Informs the user that the wifi setup failed."""
        self.__output_language_dialog("wifi_setup_failed")

    def say_internet_connection_status(self, connected: bool):
        """Display the internet status."""
        if connected:
            self.__output_language_dialog("internet_connection_ok")
            return
        self.__output_language_dialog("internet_connection_not_ok")

    def say_qtsass_not_successful(self):
        """Informs that qtsass was not set up successfully."""
        self.__output_language_dialog("qtsass_not_successful")

    def say_cocktailberry_up_to_date(self):
        """Informs that CocktailBerry is up to date."""
        self.__output_language_dialog("cocktailberry_up_to_date")

    def say_update_failed(self):
        """Informs that the update failed."""
        self.__output_language_dialog("update_failed")

    def say_create_cocktail_first(self):
        """Informs that the cocktail needs first to be created."""
        self.__output_language_dialog("create_cocktail_first")

    def say_image_processing_failed(self):
        """Informs that the image processing failed."""
        self.__output_language_dialog("image_processing_failed")

    def show_recipe_help(self):
        """Show the recipe help."""
        self.__output_language_dialog("recipe_help")

    def say_ingredient_must_be_handadd(self):
        """Informs that the ingredient must be handadd if unit is not ml."""
        self.__output_language_dialog("ingredient_must_be_handadd")

    ############################
    # Methods for prompting ####
    ############################

    def ask_to_update(self, release_information):
        """Asks the user if he wants to get the latest update."""
        message = self._choose_language("update_available")
        message = f"{message}\n\n{release_information}"
        return self.user_okay(message)

    def ask_to_start_cleaning(self):
        """Asks the user if he wants to start the cleaning process."""
        message = self._choose_language("ask_to_clean")
        return self.user_okay(message)

    def ask_to_restart_for_config(self):
        """Asks the user if he wants to restart to apply new config."""
        message = self._choose_language("restart_config")
        return self.user_okay(message)

    def ask_to_reboot(self):
        """Asks the user if he wants to reboot the system."""
        message = self._choose_language("ask_to_reboot")
        return self.user_okay(message)

    def ask_to_shutdown(self):
        """Asks the user if he wants to shutdown the system."""
        message = self._choose_language("ask_to_shutdown")
        return self.user_okay(message)

    def ask_for_backup_location(self):
        """Asks the user where to get or store the backup output."""
        message = self._choose_language("ask_for_backup_location")
        return self._get_folder_location(message)

    def ask_for_image_location(self):
        """Asks the user where to get or store the backup output."""
        message = self._choose_language("ask_for_image_location")
        return self.get_file_location(message, "Images (*.jpg *.png)")

    def ask_backup_overwrite(self, backup_files: str):
        """Asks the user if he wants to use backup."""
        message = self._choose_language("ask_backup_overwrite", backup_files=backup_files)
        return self.user_okay(message)

    def ask_enable_all_recipes(self):
        """Asks the user if he wants to set all recipes to active."""
        message = self._choose_language("ask_enable_all_recipes")
        return self.user_okay(message)

    def ask_to_adjust_time(self):
        """Asks the user if he wants to adjust the time."""
        message = self._choose_language("ask_adjust_time")
        return self.user_okay(message)

    def ask_to_export_data(self):
        """Asks the user if he wants to export the data."""
        message = self._choose_language("ask_export_data")
        return self.user_okay(message)

    def ask_to_install_qtsass(self):
        """Ask the user if he wants to install qtsass.

        Since this may take 30-60 min on the RPi, it's not done in the migrator.
        """
        message = self._choose_language("ask_to_install_qtsass")
        return self.user_okay(message)

    def ask_to_delete_x(self, x: str):
        """Ask the user if he wants to delete the given object name."""
        message = self._choose_language("ask_to_delete_x", x=x)
        return self.user_okay(message)

    def ask_to_update_system(self):
        """Asks the user if he wants to update the system."""
        message = self._choose_language("ask_to_system_update")
        return self.user_okay(message)

    def ask_to_use_reverted_pump(self):
        """Asks the user if he wants to use the reverted pump flow."""
        message = self._choose_language("ask_to_use_reverted_pump")
        return self.user_okay(message)

    def ask_to_remove_picture(self):
        """Asks the user if he wants to remove the picture."""
        message = self._choose_language("ask_to_remove_picture")
        return self.user_okay(message)


class UiLanguage:
    """Class to set the UI language to the appropriate Language."""

    def __init__(self) -> None:
        with open(LANGUAGE_FILE, encoding="UTF-8") as stream:
            self.dialogs: dict[str, dict[str, dict[str, str]]] = yaml.safe_load(stream)["ui"]

    def _choose_language(self, element_name: str, ui_element_name="generics", **kwargs) -> str:
        """Choose either the given language if exists, or english if not piping additional info into template."""
        language = cfg.UI_LANGUAGE
        ui_element = self.dialogs[ui_element_name]
        element = ui_element[element_name]
        tmpl = element.get(language, element["en"])
        return tmpl.format(**kwargs)

    def get_add_self(self) -> str:
        """Return add self label."""
        return self._choose_language("add_self", "maker")

    def get_cocktail_dummy(self) -> str:
        """Return cocktail header dummy."""
        return self._choose_language("cocktail_dummy", "maker")

    def get_add_text(self) -> str:
        """Return the add text."""
        return self._choose_language("add_button")

    def get_change_text(self) -> str:
        """Return the add text."""
        return self._choose_language("change_button")

    def get_translation(self, name: str, ui_element_name: str = "generics", **kwargs):
        """Get the translation by given key and window."""
        try:
            return self._choose_language(name, ui_element_name, **kwargs)
        except (AttributeError, KeyError):
            _logger.error(f"No translation for {name} in {ui_element_name} found")
            return ""

    def get_config_description(
        self, config_name: str, window: Literal["settings_dialog", "color_window"] = "settings_dialog"
    ) -> str:
        """Return the according description for the configuration.

        Returns empty string if there was nothing found.
        """
        try:
            return self._choose_language(config_name, window)
        # if there is nothing for this settings, we will get an attribute error
        except (AttributeError, KeyError):
            return ""

    def add_config_description(
        self,
        config_name: str,
        config_description: dict[str, str] | str,
    ):
        """Add the description to the configuration.

        description is in a dictionary, or a string.
        string: just the description in english
        dict: holding language as key, description as a value, used for translation.
        At least english (en) key needs to be provided.
        """
        # If the user only did provide a string, assign this string to english translation
        if isinstance(config_description, str):
            config_description = {"en": config_description}
        self.dialogs["settings_dialog"][config_name] = config_description

    def adjust_mainwindow(self, w: Ui_MainWindow):
        """Translate all needed elements of the main window (cocktail maker)."""
        window = "main_window"
        # iterate over tabs and set the name
        tab_names = [
            "tab_maker",
            "tab_ingredients",
            "tab_recipes",
            "tab_bottles",
        ]
        # need to start at second tab, since first is the search icon
        for i, tab_name in enumerate(tab_names, 1):
            text = self._choose_language(tab_name, window)
            w.tabWidget.setTabText(i, text)
        for ui_element, text_name in [
            (w.PBZeinzelnd, "single_ingredient_button"),
            (w.PBAvailable, "available_button"),
            (w.CHBHand, "handadd_check_label"),
            (w.label_ingredient_name, "ingredient_label"),
            (w.LAlcoholLevel, "alcohol_level_label"),
            (w.LBottleVolume, "bottle_volume_label"),
            (w.PBFlanwenden, "renew_button"),
            (w.offervirgin_checkbox, "virgin_possibility"),
            (w.label_pump_speed, "label_pump_speed"),
            (w.label_ingredient_cost, "label_ingredient_cost"),
            (w.button_set_picture, "label_picture"),
            (w.label_search_title, "header_search"),
            (w.button_enter_to_maker, "enter_to_maker"),
            (w.label_ingredient_unit, "label_ingredient_unit"),
        ]:
            ui_element.setText(self._choose_language(text_name, window))

        for ui_element, text_name in [
            (w.PBZutathinzu, "add_button"),
            (w.PBRezepthinzu, "add_button"),
            (w.PBBelegung, "change_button"),
        ]:
            ui_element.setText(self._choose_language(text_name))

    def adjust_cocktail_selection_screen(self, w: Ui_CocktailSelection):
        window = "cocktail_selection"
        w.virgin_checkbox.setText(self._choose_language("activate_virgin", window))
        w.button_back.setText(self._choose_language("back"))

    def adjust_available_windows(self, w: Ui_available):
        """Translate all needed elements of the available window."""
        window = "available_window"
        w.PBAbbruch_2.setText(self._choose_language("cancel_button"))
        w.LAvailable.setText(self._choose_language("available_label", window))
        w.LPossible.setText(self._choose_language("possible_label", window))

    def adjust_progress_screen(self, w: Ui_Progressbarwindow, cocktail_type: str):
        """Translate all needed elements of the progress window."""
        window = "progress_screen"
        w.PBabbrechen.setText(self._choose_language("cancel_button"))
        w.Labbruch.setText(self._choose_language("cancel_label", window))
        w.LProgress.setText(self._choose_language("progress_label", window))
        # w.LHeader.setText(self._choose_language(window["header_label"], cocktail_type=cocktail_type))
        if cocktail_type.lower() == "cleaning":
            cocktail_type = self._choose_language("cleaning_label", window)
        elif cocktail_type.lower() == "renew":
            cocktail_type = self._choose_language("bottle_renew_label", window)
        w.LHeader.setText(cocktail_type)

    def adjust_bonusingredient_screen(self, w: Ui_addingredient):
        """Translate all needed elements of the bonusingredient window."""
        window = "bonusingredient_screen"
        w.PBAbbrechen.setText(self._choose_language("cancel_button"))
        w.PBAusgeben.setText(self._choose_language("spend_button", window))
        w.LHeader.setText(self._choose_language("title", window))
        # w.setWindowTitle(self._choose_language("title", window))

    def adjust_bottle_window(self, w: Ui_Bottlewindow):
        """Translate all needed elements of the bottle window."""
        window = "bottle_window"
        w.PBAbbrechen.setText(self._choose_language("cancel_button"))
        w.PBEintragen.setText(self._choose_language("enter_button"))
        w.LHeader.setText(self._choose_language("header", window))

    def adjust_team_window(self, w: Ui_Teamselection):
        """Translate all needed elements of the team window."""
        window = "team_window"
        w.LHeader.setText(self._choose_language("header", window))

    def generate_numpad_header(self, header_type: Literal["amount", "alcohol", "number"] = "amount") -> str:
        """Select the header of the password window.

        header_type: 'password', 'amount', 'alcohol'.
        """
        window = "numpad_window"
        return self._choose_language(header_type, window)

    def adjust_option_window(self, w: Ui_Optionwindow):
        """Translate all needed elements of the available window."""
        window = "option_window"
        for ui_element, text_name in [
            (w.button_clean, "cleaning"),
            (w.button_config, "config"),
            (w.button_calibration, "calibration"),
            (w.button_reboot, "reboot"),
            (w.button_shutdown, "shutdown"),
            (w.button_back, "back"),
            (w.button_backup, "backup"),
            (w.button_restore, "restore"),
            (w.button_export, "data"),
            (w.button_rfid, "rfid"),
            (w.button_check_internet, "check_internet"),
        ]:
            ui_element.setText(self._choose_language(text_name, window))

    def adjust_custom_dialog(self, w: Ui_CustomDialog, use_ok: bool):
        """Translate all the labels from the datepicker window."""
        button = "ok_button" if use_ok else "close_button"
        label = self._choose_language(button)
        w.closeButton.setText(label)

    def adjust_datepicker_window(self, w: Ui_Datepicker):
        """Translate all the labels from the datepicker window."""
        window = "datepicker"
        w.header.setText(self._choose_language("header", window))

    def adjust_password_window(
        self,
        w: Ui_PasswordDialog,
        header_type: Literal["master", "maker"] = "master",
    ):
        """Translate all the labels from the password window."""
        window = "password_dialog"
        w.header.setText(self._choose_language(f"header_{header_type}_password", window))
        w.cancel_button.setText(self._choose_language("cancel_button"))
        w.enter_button.setText(self._choose_language("ok_button"))

    def adjust_custom_prompt(self, w: Ui_CustomPrompt):
        """Translate all the labels from the password window."""
        w.yes_button.setText(self._choose_language("yes_button"))
        w.no_button.setText(self._choose_language("no_button"))

    def adjust_log_window(self, w: Ui_LogWindow):
        """Translate the elements from the logs window."""
        w.button_back.setText(self._choose_language("back"))

    def adjust_rfid_reader_window(self, w: Ui_RFIDWriterWindow):
        """Translate the elements on the RFID reader window."""
        window = "rfid_writer"
        w.button_back.setText(self._choose_language("back"))
        w.button_write.setText(self._choose_language("write", window))
        w.label_information.setText(self._choose_language("start_text", window))

    def get_rfid_information_display(self, element: Literal["success", "prompt", "error"]):
        """Return the information element for rfid."""
        return self._choose_language(element, "rfid_writer")

    def adjust_wifi_window(self, w: Ui_WiFiWindow):
        """Translate the elements on the RFID reader window."""
        window = "wifi"
        w.button_back.setText(self._choose_language("back"))
        w.button_enter.setText(self._choose_language("enter_button"))
        w.label_ssid.setText(self._choose_language("ssid", window))
        w.label_password.setText(self._choose_language("password", window))

    def adjust_color_window(self, w: Ui_ColorWindow):
        """Translate the elements of the custom color window."""
        window = "color_window"
        w.button_back.setText(self._choose_language("back"))
        w.button_apply.setText(self._choose_language("apply"))
        w.button_use_template.setText(self._choose_language("use_template", window))
        w.label_description.setText(self._choose_language("description", window))

    def adjust_addon_window(self, w: Ui_Addonwindow):
        """Translate the elements of the addon window."""
        window = "addon_window"
        w.button_back.setText(self._choose_language("back"))
        w.button_manage.setText(self._choose_language("manage", window))

    def get_no_addon_gui_info(self):
        return self._choose_language("no_gui", "addon_window")

    def adjust_addon_manager(self, w: Ui_AddonManager):
        """Translate the elements of the addon manager."""
        w.button_back.setText(self._choose_language("back"))
        w.button_apply.setText(self._choose_language("apply"))

    def adjust_data_window(self, w: Ui_DataWindow):
        """Translate the elements of the data window."""
        window = "data_window"
        w.button_back.setText(self._choose_language("back"))
        w.button_reset.setText(self._choose_language("export", window))

    def adjust_picture_window(self, w: Ui_PictureWindow, cocktail: str):
        """Translate the elements of the search window."""
        window = "picture_window"
        w.label_titel.setText(self._choose_language("header", window, cocktail=cocktail))
        w.button_back.setText(self._choose_language("back"))
        w.button_enter.setText(self._choose_language("apply"))

    def adjust_config_window(self, w: Ui_ConfigWindow):
        """Translate the elements of the addon manager."""
        w.button_back.setText(self._choose_language("back"))
        w.button_save.setText(self._choose_language("apply"))

    def adjust_refill_prompt(
        self,
        w: Ui_RefillPrompt,
        ingredient_name: str,
        ingredient_volume: int,
        needed_volume: int,
    ):
        """Translate the elements of the refill prompt."""
        window = "refill_prompt"
        w.button_later.setText(self._choose_language("later", window))
        w.button_to_bottles.setText(self._choose_language("to_bottles", window))
        w.button_apply.setText(self._choose_language("apply"))
        w.checkbox_done.setText(self._choose_language("done"))
        w.label_message.setText(
            self._choose_language(
                "information",
                window,
                ingredient_name=ingredient_name,
                ingredient_volume=ingredient_volume,
                needed_volume=needed_volume,
            )
        )


UI_LANGUAGE = UiLanguage()
DIALOG_HANDLER = DialogHandler()
