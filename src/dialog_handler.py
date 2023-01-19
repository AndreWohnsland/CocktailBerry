# otherwise circular import :(
# pylint: disable=import-outside-toplevel

from pathlib import Path
from typing import Dict, List, Optional, Literal
import yaml
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QWidget
from PyQt5.QtCore import Qt
from src.config_manager import CONFIG as cfg


DIRPATH = Path(__file__).parent.absolute()
LANGUAGE_FILE = DIRPATH / "language.yaml"


class DialogHandler():
    """Class to hold all the dialogues for the popups and language settings"""

    def __init__(self) -> None:
        self.icon_path = str(DIRPATH / "ui_elements" / "Cocktail-icon.png")
        with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
            self.dialogs: Dict[str, Dict[str, str]] = yaml.safe_load(stream)["dialog"]

    def __choose_language(self, element_name: str, **kwargs) -> str:
        """Choose either the given language if exists, or english if not piping additional info into template"""
        language = cfg.UI_LANGUAGE
        element = self.dialogs[element_name]
        tmpl = element.get(language, element["en"])
        return tmpl.format(**kwargs)

    def standard_box(self, message: str, title: str = "", use_ok=False):
        """ The default messagebox for the Maker. Uses a Custom QDialog with Close-Button """
        from src.ui.setup_custom_dialog import CustomDialog
        if not title:
            title = self.__choose_language("box_title")
        fill_string = "-" * 70
        fancy_message = f"{fill_string}\n{message}\n{fill_string}"
        messagebox = CustomDialog(fancy_message, title, self.icon_path, use_ok)
        messagebox.exec_()

    def user_okay(self, text: str):
        msg_box = QMessageBox()
        msg_box.setText(text)
        msg_box.setWindowTitle(self.__choose_language("confirmation_required"))
        yes_text = self.__choose_language("yes_button")
        no_text = self.__choose_language("no_button")
        yes_button = msg_box.addButton(yes_text, QMessageBox.YesRole)  # type: ignore
        yes_button.setProperty("cssClass", "btn-inverted")
        no_button = msg_box.addButton(no_text, QMessageBox.NoRole)  # type: ignore
        no_button.setProperty("cssClass", "btn-inverted")
        style_sheet = str(DIRPATH / "ui" / "styles" / f"{cfg.MAKER_THEME}.css")
        with open(style_sheet, "r", encoding="utf-8") as file_handler:
            msg_box.setStyleSheet(file_handler.read())
        msg_box.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # type: ignore
        msg_box.move(50, 50)
        msg_box.exec_()
        if msg_box.clickedButton() == yes_button:
            return True
        return False

    def password_prompt(self):
        """Opens a password prompt, return if successful entered password"""
        from src.ui.setup_password_dialog import PasswordDialog
        password_dialog = PasswordDialog()
        if password_dialog.exec_():
            return True
        return False

    def __output_language_dialog(self, dialog_name: str, use_ok=False, **kwargs):
        msg = self.__choose_language(dialog_name, **kwargs)
        self.standard_box(msg, use_ok=use_ok)

    def _get_folder_location(self, w: QWidget, message: str):
        return QFileDialog.getExistingDirectory(w, message)

    ############################
    # Methods for creating msg #
    ############################
    def say_wrong_password(self):
        """Informs user that the password is wrong"""
        self.__output_language_dialog("wrong_password")

    def say_supply_water(self):
        """Informs user that enough water needs to be supplied for cleaning"""
        self.__output_language_dialog("supply_water", True)

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

    def say_ingredient_added_or_changed(self, ingredient_name: str, new_ingredient: bool, selected_ingredient: Optional[str] = None):
        """Informs user that the ingredient was added or altered"""
        if new_ingredient:
            self.__say_ingredient_added(ingredient_name)
        else:
            self.__say_ingredient_changed(selected_ingredient, ingredient_name)

    def say_cocktail_canceled(self):
        """Informs user that the cocktail was canceled"""
        self.__output_language_dialog("cocktail_canceled")

    def say_cocktail_ready(self, comment: str):
        """Informs user that the cocktail is done with additional information what to add"""
        full_comment = ""
        if comment:
            header_comment = self.__choose_language("cocktail_ready_add")
            full_comment = f"\n\n{header_comment}{comment}"
        self.__output_language_dialog("cocktail_ready", full_comment=full_comment)

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
        self.__output_language_dialog(
            "python_deprecated",
            sys_python=sys_python,
            program_python=program_python
        )

    def ask_to_update(self):
        """Asks the user if he wants to get the latest update"""
        message = self.__choose_language("update_available")
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

    def ask_backup_overwrite(self):
        """Asks the user if he wants to use backup"""
        message = self.__choose_language("ask_backup_overwrite")
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

    def adjust_mainwindow(self, w):
        """Translates all needed elements of the main window (cocktail maker)"""
        window = "main_window"
        # iterate over tabs and set the name
        tab_names = [
            "tab_maker",
            "tab_ingredients",
            "tab_recipes",
            "tab_bottles",
        ]
        for i, tab_name in enumerate(tab_names):
            text = self.__choose_language(tab_name, window)
            w.tabWidget.setTabText(i, text)
        for ui_element, text_name in [
            (w.PBZubereiten_custom, "prepare_button"),
            (w.PBZeinzelnd, "single_ingredient_button"),
            (w.PBAvailable, "available_button"),
            (w.PBZutathinzu, "add_button"),
            (w.CHBHand, "handadd_check_label"),
            (w.LIngredient, "ingredient_label"),
            (w.LAlcoholLevel, "alcohol_level_label"),
            (w.LBottleVolume, "bottle_volume_label"),
            (w.LRHandAdd, "hand_add_label"),
            (w.PBRezepthinzu, "add_button"),
            (w.PBBelegung, "change_button"),
            (w.PBFlanwenden, "renew_button"),
            (w.virgin_checkbox, "activate_virgin"),
            (w.offervirgin_checkbox, "virgin_possibility"),
        ]:
            ui_element.setText(self.__choose_language(text_name, window))

    def adjust_available_windows(self, w):
        """Translates all needed elements of the available window"""
        window = "available_window"
        w.PBAbbruch_2.setText(self.__choose_language("cancel_button"))
        w.LAvailable.setText(self.__choose_language("available_label", window))
        w.LPossible.setText(self.__choose_language("possible_label", window))

    def adjust_handadds_window(self, w):
        """Translates all needed elements of the handadds window"""
        window = "handadds_window"
        w.PBAbbrechen.setText(self.__choose_language("cancel_button"))
        w.PBEintragen.setText(self.__choose_language("enter_button"))
        w.LHeader.setText(self.__choose_language("title", window))
        w.setWindowTitle(self.__choose_language("title", window))

    def adjust_progress_screen(self, w, cocktail_type: str):
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

    def adjust_bonusingredient_screen(self, w):
        """Translates all needed elements of the bonusingredient window"""
        window = "bonusingredient_screen"
        w.PBAbbrechen.setText(self.__choose_language("cancel_button"))
        w.PBAusgeben.setText(self.__choose_language("spend_button", window))
        w.LHeader.setText(self.__choose_language("title", window))
        w.setWindowTitle(self.__choose_language("title", window))

    def adjust_bottle_window(self, w):
        """Translates all needed elements of the bottle window"""
        window = "bottle_window"
        w.PBAbbrechen.setText(self.__choose_language("cancel_button"))
        w.PBEintragen.setText(self.__choose_language("enter_button"))
        w.LHeader.setText(self.__choose_language("header", window))

    def adjust_team_window(self, w):
        """Translates all needed elements of the team window"""
        window = "team_window"
        w.LHeader.setText(self.__choose_language("header", window))

    def generate_numpad_header(self, header_type: Literal['amount', 'alcohol'] = "amount") -> str:
        """Selects the header of the password window.
        header_type: 'password', 'amount', 'alcohol'
        """
        window = "numpad_window"
        if header_type == "amount":
            return self.__choose_language("amount", window)
        if header_type == "alcohol":
            return self.__choose_language("alcohol", window)
        raise ValueError("Currently not possible")

    def adjust_option_window(self, w):
        """Translates all needed elements of the available window"""
        window = "option_window"
        for ui_element, text_name in [
            (w.button_clean, "cleaning"),
            (w.button_config, "config"),
            (w.button_back, "back"),
            (w.button_calibration, "calibration"),
            (w.button_reboot, "reboot"),
            (w.button_shutdown, "shutdown"),
            (w.button_export, "export"),
        ]:
            ui_element.setText(self.__choose_language(text_name, window))

    def adjust_custom_dialog(self, w, use_ok: bool):
        """Translate all the labels from the datepicker window"""
        if use_ok:
            label = self.__choose_language("ok_button")
        else:
            label = self.__choose_language("close_button")
        w.closeButton.setText(label)

    def adjust_datepicker_window(self, w):
        """Translate all the labels from the datepicker window"""
        window = "datepicker"
        w.header.setText(self.__choose_language("header", window))

    def adjust_password_window(self, w):
        """Translate all the labels from the password window"""
        window = "password_dialog"
        w.header.setText(self.__choose_language("header", window))
        w.cancel_button.setText(self.__choose_language("cancel_button"))
        w.enter_button.setText(self.__choose_language("ok_button"))


UI_LANGUAGE = UiLanguage()
