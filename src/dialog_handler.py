# otherwise circular import :(
# pylint: disable=import-outside-toplevel

from __future__ import annotations
from pathlib import Path
import time
from typing import Dict, List, Optional, Literal, TYPE_CHECKING, Union
from threading import Thread, Event
import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QWidget, QDialog
from src.config_manager import CONFIG as cfg
from src.logger_handler import LoggerHandler
from src.ui_elements.addonmanager import Ui_AddonManager
from src.utils import get_platform_data
from src.filepath import LANGUAGE_FILE, APP_ICON_FILE
from src import __version__

if TYPE_CHECKING:
    from src.ui_elements import (
        Ui_available, Ui_addingredient, Ui_Bottlewindow, Ui_MainWindow, Ui_CustomDialog,
        Ui_CustomPrompt, Ui_Datepicker, Ui_LogWindow, Ui_Optionwindow,
        Ui_PasswordDialog, Ui_Progressbarwindow, Ui_RFIDWriterWindow, Ui_Teamselection,
        Ui_WiFiWindow, Ui_ColorWindow, Ui_Addonwindow, Ui_DataWindow,
        Ui_CocktailSelection, Ui_PictureWindow
    )

_logger = LoggerHandler("dialog_handler")


class DialogHandler():
    """Class to hold all the dialogues for the popups and language settings"""

    def __init__(self) -> None:
        self.icon_path = str(APP_ICON_FILE)
        with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
            self.dialogs: Dict[str, Dict[str, str]] = yaml.safe_load(stream)["dialog"]

    def __choose_language(self, element_name: str, **kwargs) -> str:
        """Choose either the given language if exists, or english if not piping additional info into template"""
        language = cfg.UI_LANGUAGE
        element = self.dialogs[element_name]
        tmpl = element.get(language, element["en"])
        return tmpl.format(**kwargs)

    def standard_box(self, message: str, title: str = "", use_ok=False, close_time: Optional[int] = None):
        """ The default messagebox for the Maker. Uses a Custom QDialog with Close-Button """
        from src.ui.setup_custom_dialog import CustomDialog

        def close_thread(event: Event, box: CustomDialog, close_time: int):
            """Function to control auto close"""
            time.sleep(close_time)
            if event.is_set():
                return
            box.close()

        if not title:
            title = self.__choose_language("box_title")
        fill_string = "-" * 70
        fancy_message = f"{fill_string}\n{message}\n{fill_string}"
        messagebox = CustomDialog(fancy_message, title, use_ok)
        event = Event()
        # If there is a close time, start auto close
        if close_time is not None:
            auto_closer = Thread(target=close_thread, args=(event, messagebox, close_time), daemon=True)
            auto_closer.start()
        messagebox.exec_()
        # Need to set event, in case thread is still waiting
        event.set()

    def user_okay(self, text: str):
        """Prompts the user for the given message and asks for confirmation

        Args:
            text (str): Text to be displayed

        Returns:
            bool: If the user accepted the prompted message
        """
        from src.ui.setup_custom_prompt import CustomPrompt
        msg_box = CustomPrompt(text)
        if msg_box.exec_():
            return True
        return False

    def password_prompt(
        self,
        right_password: int = cfg.UI_MASTERPASSWORD,
        header_type: Literal['master', 'maker'] = "master",
    ):
        """Opens a password prompt, return if successful entered password
        Option to also use other than master password
        This is useful for example for the UI_MAKER_PASSWORD, or if needed for more things in the future
        """
        from src.ui.setup_password_dialog import PasswordDialog
        # if password is empty, return true
        # Empty means zero in this case, since the config is an int
        if right_password == 0:
            return True
        password_dialog = PasswordDialog(right_password, header_type)
        if password_dialog.exec_():
            return True
        return False

    def __output_language_dialog(self, dialog_name: str, use_ok=False, close_time: Optional[int] = None, **kwargs):
        msg = self.__choose_language(dialog_name, **kwargs)
        self.standard_box(msg, use_ok=use_ok, close_time=close_time)

    def _generate_file_dialog(self, w: QWidget, message: str = ""):
        """Creates the base file dialog and shows it with the full screen settings"""
        file_dialog = QFileDialog(w)
        file_dialog.setWindowTitle(message)
        file_dialog.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint  # type: ignore
        )
        if not cfg.UI_DEVENVIRONMENT:
            file_dialog.setCursor(Qt.BlankCursor)  # type: ignore
        file_dialog.showMaximized()
        file_dialog.setFixedSize(cfg.UI_WIDTH, cfg.UI_HEIGHT)
        file_dialog.resize(cfg.UI_WIDTH, cfg.UI_HEIGHT)
        file_dialog.move(0, 0)
        return file_dialog

    def _parse_file_dialog(self, file_dialog: QFileDialog):
        """Extracts the selected file/folder from the file dialog"""
        if file_dialog.exec_() == QDialog.Accepted:  # type: ignore
            file_name = file_dialog.selectedFiles()[0]  # get the selected file
            # Qt will return empty string if user cancels the dialog
            if file_name:
                return Path(file_name).absolute()
        return None

    def _get_folder_location(self, w: QWidget, message: str):
        """Returns the selected folder"""
        file_dialog = self._generate_file_dialog(w, message)
        file_dialog.setFileMode(QFileDialog.Directory)  # type: ignore
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)  # type: ignore
        return self._parse_file_dialog(file_dialog)

    def get_file_location(self, w: QWidget, message: str, filter_str: str):
        """Returns the selected file"""
        file_dialog = self._generate_file_dialog(w, message)
        file_dialog.setFileMode(QFileDialog.ExistingFile)  # type: ignore
        file_dialog.setNameFilter(filter_str)
        return self._parse_file_dialog(file_dialog)

    ############################
    # Methods for creating msg #
    ############################

    def say_wrong_password(self):
        """Informs user that the password is wrong"""
        self.__output_language_dialog("wrong_password")

    def say_done(self):
        """Informs user that process is done"""
        self.__output_language_dialog("done")

    def say_bottles_renewed(self):
        """Informs user that the bottles have been renewed"""
        self.__output_language_dialog("bottles_renewed")

    def say_no_recipe_selected(self):
        """Informs user that no recipe is selected"""
        self.__output_language_dialog("no_recipe_selected")

    def say_no_ingredient_selected(self):
        """Informs user that no ingredient is selected"""
        self.__output_language_dialog("no_ingredient_selected")

    def say_ingredient_still_at_bottle(self):
        """Informs user that the ingredient is still used at a bottle"""
        self.__output_language_dialog("ingredient_still_at_bottle")

    def say_ingredient_still_at_recipe(self, recipe_string: str):
        """Informs user that the ingredient is still used in a recipe"""
        self.__output_language_dialog("ingredient_still_at_recipe", recipe_string=recipe_string)

    def say_ingredient_still_as_machine_in_recipe(self, recipe_list: List[str]):
        """Informs user that the ingredient is still used in a recipe as machine add"""
        formatted_string = ", ".join(recipe_list)
        self.__output_language_dialog("ingredient_still_as_machine_add", recipe_list=formatted_string)

    def say_ingredient_double_usage(self, ingredient_name: str):
        """Informs user that the ingredient is already used at least one other time"""
        self.__output_language_dialog("ingredient_double_usage", ingredient_name=ingredient_name)

    def say_ingredient_deleted(self, ingredient_name: str):
        """Informs user that the ingredient was deleted"""
        self.__output_language_dialog("ingredient_deleted", ingredient_name=ingredient_name)

    def __say_ingredient_added(self, ingredient_name: str):
        """Informs user that the ingredient was added to the database"""
        self.__output_language_dialog("ingredient_added", ingredient_name=ingredient_name)

    def __say_ingredient_changed(self, selected_ingredient: Optional[str], ingredient_name: str):
        """Informs user that the ingredient was changed"""
        self.__output_language_dialog(
            "ingredient_changed",
            selected_ingredient=selected_ingredient,
            ingredient_name=ingredient_name
        )

    def say_ingredient_added_or_changed(
        self,
        ingredient_name: str,
        new_ingredient: bool,
        selected_ingredient: Optional[str] = None
    ):
        """Informs user that the ingredient was added or altered"""
        if new_ingredient:
            self.__say_ingredient_added(ingredient_name)
        else:
            self.__say_ingredient_changed(selected_ingredient, ingredient_name)

    def say_cocktail_canceled(self):
        """Informs user that the cocktail was canceled"""
        self.__output_language_dialog("cocktail_canceled", close_time=10)

    def say_cocktail_ready(self, comment: str):
        """Informs user that the cocktail is done with additional information what to add"""
        # no more message if there is no additional information
        if not comment:
            return
        close_time = 60
        header_comment = self.__choose_language("cocktail_ready_add")
        full_comment = f"\n\n{header_comment}{comment}"
        self.__output_language_dialog("cocktail_ready", close_time=close_time, full_comment=full_comment)

    def say_enter_cocktail_name(self):
        """Informs user that no cocktail name was supplied"""
        self.__output_language_dialog("enter_cocktail_name")

    def say_recipe_deleted(self, recipe_name: str):
        """Informs user that the recipe was deleted"""
        self.__output_language_dialog("recipe_deleted", recipe_name=recipe_name)

    def say_all_recipes_enabled(self):
        """Informs user that all recipes have been enabled"""
        self.__output_language_dialog("all_recipes_enabled")

    def say_recipe_added(self, recipe_name: str):
        """Informs user that the recipe was added to the database"""
        self.__output_language_dialog("recipe_added", recipe_name=recipe_name)

    def say_recipe_updated(self, old_name: str, new_name: str):
        """Informs user that the recipe was updated"""
        self.__output_language_dialog("recipe_updated", old_name=old_name, new_name=new_name)

    def say_recipe_at_least_one_ingredient(self):
        """Informs user that the recipe got no according ingredients"""
        self.__output_language_dialog("recipe_at_least_one_ingredient")

    def say_all_data_exported(self, file_path: str):
        """Informs user that all data have been exported"""
        self.__output_language_dialog("all_data_exported", file_path=file_path)

    def say_not_enough_ingredient_volume(self, ingredient_name: str, level: int, volume: int):
        """Informs user that the ingredient got not enough volume for cocktail"""
        level = max(0, level)
        self.__output_language_dialog(
            "not_enough_ingredient_volume",
            ingredient_name=ingredient_name,
            volume=volume,
            level=level
        )

    def say_name_already_exists(self):
        """Informs user that there is already an entry in the DB with that name"""
        self.__output_language_dialog("name_already_exists")

    def say_some_value_missing(self, value: Optional[str] = None):
        """Informs user that he missed at least one value"""
        if value is None:
            self.__output_language_dialog("some_value_missing")
        else:
            self.__output_language_dialog("some_value_missing_specific", value=value)

    def say_needs_to_be_int(self, value: Optional[str] = None):
        """Informs user that the given value is not a number"""
        if value is None:
            self.__output_language_dialog("needs_to_be_int")
        else:
            self.__output_language_dialog("needs_to_be_int_specific", value=value)

    def say_alcohol_level_max_limit(self):
        """Informs user that the alcohol level can not be greater than 100"""
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
        """Informs that the given system python is older than the
        recommended python for the program"""
        self.__output_language_dialog(
            "python_deprecated",
            sys_python=sys_python,
            program_python=program_python
        )

    def say_welcome_message(self):
        """Displays the welcome dialog, show version and platform info"""
        self.__output_language_dialog(
            "welcome_dialog",
            version=__version__,
            platform=get_platform_data()
        )

    def say_wifi_entered(self, success: bool, ssid: str, password: str):
        """Informs the user about the wifi enter process"""
        if success:
            self.__output_language_dialog("wifi_success")
            return
        self.__output_language_dialog(
            "wifi_failure",
            ssid=ssid,
            password=password,
        )

    def say_wifi_setup_failed(self):
        """Informs the user that the wifi setup failed"""
        self.__output_language_dialog("wifi_setup_failed")

    def say_internet_connection_status(self, connected: bool):
        """Displays the internet status"""
        if connected:
            self.__output_language_dialog("internet_connection_ok")
            return
        self.__output_language_dialog("internet_connection_not_ok")

    def say_qtsass_not_successful(self):
        """Informs that qtsass was not set up successfully"""
        self.__output_language_dialog("qtsass_not_successful")

    def say_cocktailberry_up_to_date(self):
        """Informs that cocktailberry is up to date"""
        self.__output_language_dialog("cocktailberry_up_to_date")

    def say_update_failed(self):
        """Informs that the update failed"""
        self.__output_language_dialog("update_failed")

    def say_create_cocktail_first(self):
        """Informs that the cocktail needs first to be created"""
        self.__output_language_dialog("create_cocktail_first")

    def say_image_processing_failed(self):
        """Informs that the image processing failed"""
        self.__output_language_dialog("image_processing_failed")

    def show_recipe_help(self):
        """Shows the recipe help"""
        self.__output_language_dialog("recipe_help")

    def say_ingredient_must_be_handadd(self):
        """Informs that the ingredient must be handadd if unit is not ml"""
        self.__output_language_dialog("ingredient_must_be_handadd")

    ############################
    # Methods for prompting ####
    ############################

    def ask_to_update(self, release_information):
        """Asks the user if he wants to get the latest update"""
        message = self.__choose_language("update_available")
        message = f"{message}\n\n{release_information}"
        return self.user_okay(message)

    def ask_to_start_cleaning(self):
        """Asks the user if he wants to start the cleaning process"""
        message = self.__choose_language("ask_to_clean")
        return self.user_okay(message)

    def ask_to_restart_for_config(self):
        """Asks the user if he wants to restart to apply new config"""
        message = self.__choose_language("restart_config")
        return self.user_okay(message)

    def ask_to_reboot(self):
        """Asks the user if he wants to reboot the system"""
        message = self.__choose_language("ask_to_reboot")
        return self.user_okay(message)

    def ask_to_shutdown(self):
        """Asks the user if he wants to shutdown the system"""
        message = self.__choose_language("ask_to_shutdown")
        return self.user_okay(message)

    def ask_for_backup_location(self, w: QWidget):
        """Asks the user where to get or store the backup output"""
        message = self.__choose_language("ask_for_backup_location")
        return self._get_folder_location(w, message)

    def ask_for_image_location(self, w: QWidget):
        """Asks the user where to get or store the backup output"""
        message = self.__choose_language("ask_for_image_location")
        return self.get_file_location(w, message, "Images (*.jpg *.png)")

    def ask_backup_overwrite(self, backup_files: str):
        """Asks the user if he wants to use backup"""
        message = self.__choose_language("ask_backup_overwrite", backup_files=backup_files)
        return self.user_okay(message)

    def ask_enable_all_recipes(self):
        """Asks the user if he wants to set all recipes to active"""
        message = self.__choose_language("ask_enable_all_recipes")
        return self.user_okay(message)

    def ask_to_adjust_time(self):
        """Asks the user if he wants to adjust the time"""
        message = self.__choose_language("ask_adjust_time")
        return self.user_okay(message)

    def ask_to_export_data(self):
        """Asks the user if he wants to export the data"""
        message = self.__choose_language("ask_export_data")
        return self.user_okay(message)

    def ask_to_install_qtsass(self):
        """Asks the user if he wants to install qtsass
        Since this may take 30-60 min on the RPi, it's not done in the migrator.
        """
        message = self.__choose_language("ask_to_install_qtsass")
        return self.user_okay(message)

    def ask_to_delete_x(self, x: str):
        """Ask the user if he wants to delete the given object name"""
        message = self.__choose_language("ask_to_delete_x", x=x)
        return self.user_okay(message)

    def ask_to_update_system(self):
        """Asks the user if he wants to update the system"""
        message = self.__choose_language("ask_to_system_update")
        return self.user_okay(message)

    def ask_to_use_reverted_pump(self):
        """Asks the user if he wants to use the reverted pump flow"""
        message = self.__choose_language("ask_to_use_reverted_pump")
        return self.user_okay(message)

    def ask_to_remove_picture(self):
        """Asks the user if he wants to remove the picture"""
        message = self.__choose_language("ask_to_remove_picture")
        return self.user_okay(message)


class UiLanguage():
    """Class to set the UI language to the appropriate Language"""

    def __init__(self) -> None:
        with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
            self.dialogs: Dict[str, Dict[str, Dict[str, str]]] = yaml.safe_load(stream)["ui"]

    def __choose_language(self, element_name: str, ui_element_name="generics", **kwargs) -> str:
        """Choose either the given language if exists, or english if not piping additional info into template"""
        language = cfg.UI_LANGUAGE
        ui_element = self.dialogs[ui_element_name]
        element = ui_element[element_name]
        tmpl = element.get(language, element["en"])
        return tmpl.format(**kwargs)

    def get_add_self(self) -> str:
        """Returns add self label"""
        return self.__choose_language("add_self", "maker")

    def get_cocktail_dummy(self) -> str:
        """Returns cocktail header dummy"""
        return self.__choose_language("cocktail_dummy", "maker")

    def get_add_text(self) -> str:
        """Returns the add text"""
        return self.__choose_language("add_button")

    def get_change_text(self) -> str:
        """Returns the add text"""
        return self.__choose_language("change_button")

    def get_translation(self, name: str, ui_element_name: str = "generics"):
        """Gets the translation by given key and window"""
        try:
            return self.__choose_language(name, ui_element_name)
        except (AttributeError, KeyError):
            _logger.error(f"No translation for {name} in {ui_element_name} found")
            return ""

    def get_config_description(
            self,
            config_name: str,
            window: Literal["settings_dialog", "color_window"] = "settings_dialog") -> str:
        """Returns the according description for the configuration.
        Returns empty string if there was nothing found
        """
        try:
            return self.__choose_language(config_name, window)
        # if there is nothing for this settings, we will get an attribute error
        except (AttributeError, KeyError):
            return ""

    def add_config_description(
        self,
        config_name: str,
        config_description: Union[dict[str, str], str],
    ):
        """Adds the description to the configuration.
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
        """Translates all needed elements of the main window (cocktail maker)"""
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
            text = self.__choose_language(tab_name, window)
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
            (w.check_slow_ingredient, "slow_ingredient_check_label"),
            (w.label_ingredient_cost, "label_ingredient_cost"),
            (w.button_set_picture, "label_picture"),
            (w.label_search_title, "header_search"),
            (w.button_enter_to_maker, "enter_to_maker"),
            (w.label_ingredient_unit, "label_ingredient_unit"),
        ]:
            ui_element.setText(self.__choose_language(text_name, window))

        for ui_element, text_name in [
            (w.PBZutathinzu, "add_button"),
            (w.PBRezepthinzu, "add_button"),
            (w.PBBelegung, "change_button"),
        ]:
            ui_element.setText(self.__choose_language(text_name))

    def adjust_cocktail_selection_screen(self, w: Ui_CocktailSelection):
        window = "cocktail_selection"
        w.prepare_button.setText(self.__choose_language("prepare_button", window))
        w.virgin_checkbox.setText(self.__choose_language("activate_virgin", window))
        w.button_back.setText(self.__choose_language("back"))

    def adjust_available_windows(self, w: Ui_available):
        """Translates all needed elements of the available window"""
        window = "available_window"
        w.PBAbbruch_2.setText(self.__choose_language("cancel_button"))
        w.LAvailable.setText(self.__choose_language("available_label", window))
        w.LPossible.setText(self.__choose_language("possible_label", window))

    def adjust_progress_screen(self, w: Ui_Progressbarwindow, cocktail_type: str):
        """Translates all needed elements of the progress window"""
        window = "progress_screen"
        w.PBabbrechen.setText(self.__choose_language("cancel_button"))
        w.Labbruch.setText(self.__choose_language("cancel_label", window))
        w.LProgress.setText(self.__choose_language("progress_label", window))
        # w.LHeader.setText(self.__choose_language(window["header_label"], cocktail_type=cocktail_type))
        if cocktail_type.lower() == "cleaning":
            cocktail_type = self.__choose_language("cleaning_label", window)
        elif cocktail_type.lower() == "renew":
            cocktail_type = self.__choose_language("bottle_renew_label", window)
        w.LHeader.setText(cocktail_type)

    def adjust_bonusingredient_screen(self, w: Ui_addingredient):
        """Translates all needed elements of the bonusingredient window"""
        window = "bonusingredient_screen"
        w.PBAbbrechen.setText(self.__choose_language("cancel_button"))
        w.PBAusgeben.setText(self.__choose_language("spend_button", window))
        w.LHeader.setText(self.__choose_language("title", window))
        # w.setWindowTitle(self.__choose_language("title", window))

    def adjust_bottle_window(self, w: Ui_Bottlewindow):
        """Translates all needed elements of the bottle window"""
        window = "bottle_window"
        w.PBAbbrechen.setText(self.__choose_language("cancel_button"))
        w.PBEintragen.setText(self.__choose_language("enter_button"))
        w.LHeader.setText(self.__choose_language("header", window))

    def adjust_team_window(self, w: Ui_Teamselection):
        """Translates all needed elements of the team window"""
        window = "team_window"
        w.LHeader.setText(self.__choose_language("header", window))

    def generate_numpad_header(self, header_type: Literal['amount', 'alcohol', 'number'] = "amount") -> str:
        """Selects the header of the password window.
        header_type: 'password', 'amount', 'alcohol'
        """
        window = "numpad_window"
        return self.__choose_language(header_type, window)

    def adjust_option_window(self, w: Ui_Optionwindow):
        """Translates all needed elements of the available window"""
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
            ui_element.setText(self.__choose_language(text_name, window))

    def adjust_custom_dialog(self, w: Ui_CustomDialog, use_ok: bool):
        """Translate all the labels from the datepicker window"""
        if use_ok:
            label = self.__choose_language("ok_button")
        else:
            label = self.__choose_language("close_button")
        w.closeButton.setText(label)

    def adjust_datepicker_window(self, w: Ui_Datepicker):
        """Translate all the labels from the datepicker window"""
        window = "datepicker"
        w.header.setText(self.__choose_language("header", window))

    def adjust_password_window(
        self,
        w: Ui_PasswordDialog,
        header_type: Literal['master', 'maker'] = "master",
    ):
        """Translate all the labels from the password window"""
        window = "password_dialog"
        w.header.setText(self.__choose_language(f"header_{header_type}_password", window))
        w.cancel_button.setText(self.__choose_language("cancel_button"))
        w.enter_button.setText(self.__choose_language("ok_button"))

    def adjust_custom_prompt(self, w: Ui_CustomPrompt):
        """Translate all the labels from the password window"""
        w.yes_button.setText(self.__choose_language("yes_button"))
        w.no_button.setText(self.__choose_language("no_button"))

    def adjust_log_window(self, w: Ui_LogWindow):
        """Translates the elements from the logs window"""
        w.button_back.setText(self.__choose_language("back"))

    def adjust_rfid_reader_window(self, w: Ui_RFIDWriterWindow):
        """Translates the elements on the RFID reader window"""
        window = "rfid_writer"
        w.button_back.setText(self.__choose_language("back"))
        w.button_write.setText(self.__choose_language("write", window))
        w.label_information.setText(self.__choose_language("start_text", window))

    def get_rfid_information_display(self, element: Literal['success', 'prompt', 'error']):
        """Returns the information element for rfid"""
        return self.__choose_language(element, "rfid_writer")

    def adjust_wifi_window(self, w: Ui_WiFiWindow):
        """Translates the elements on the RFID reader window"""
        window = "wifi"
        w.button_back.setText(self.__choose_language("back"))
        w.button_enter.setText(self.__choose_language("enter_button"))
        w.label_ssid.setText(self.__choose_language("ssid", window))
        w.label_password.setText(self.__choose_language("password", window))

    def adjust_color_window(self, w: Ui_ColorWindow):
        """Translates the elements of the custom color window"""
        window = "color_window"
        w.button_back.setText(self.__choose_language("back"))
        w.button_apply.setText(self.__choose_language("apply"))
        w.button_use_template.setText(self.__choose_language("use_template", window))
        w.label_description.setText(self.__choose_language("description", window))

    def adjust_addon_window(self, w: Ui_Addonwindow):
        """"Translates the elements of the addon window"""
        window = "addon_window"
        w.button_back.setText(self.__choose_language("back"))
        w.button_manage.setText(self.__choose_language("manage", window))

    def get_no_addon_gui_info(self):
        return self.__choose_language("no_gui", "addon_window")

    def adjust_addon_manager(self, w: Ui_AddonManager):
        """"Translates the elements of the addon manager"""
        w.button_back.setText(self.__choose_language("back"))
        w.button_apply.setText(self.__choose_language("apply"))

    def adjust_data_window(self, w: Ui_DataWindow):
        """"Translates the elements of the data window"""
        window = "data_window"
        w.button_back.setText(self.__choose_language("back"))
        w.button_reset.setText(self.__choose_language("export", window))

    def adjust_picture_window(self, w: Ui_PictureWindow, cocktail: str):
        """Translates the elements of the search window"""
        window = "picture_window"
        w.label_titel.setText(self.__choose_language("header", window, cocktail=cocktail))
        w.button_back.setText(self.__choose_language("back"))
        w.button_enter.setText(self.__choose_language("apply"))


UI_LANGUAGE = UiLanguage()
