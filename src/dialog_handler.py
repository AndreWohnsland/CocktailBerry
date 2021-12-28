import os
from typing import List, Union
import yaml
from src.config_manager import ConfigManager

DIRPATH = os.path.dirname(os.path.abspath(__file__))
LANGUAGE_FILE = os.path.join(DIRPATH, "language.yaml")


class DialogHandler(ConfigManager):
    """Class to hold all the dialoges for the popups and language settings"""

    def __init__(self) -> None:
        super().__init__()
        self.icon_path = os.path.join(DIRPATH, "..", "ui_elements", "Cocktail-icon.png")
        with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
            self.dialogs = yaml.safe_load(stream)["dialog"]

    def __choose_language(self, element: dict, **kwargs) -> str:
        """Choose either the given language if exists, or english if not piping additional info into template"""
        language = self.UI_LANGUAGE
        tmpl = element.get(language, element["en"])
        return tmpl.format(**kwargs)

    def standard_box(self, message: str, title: str = None):
        """ The default messagebox for the Maker. Uses a Custom QDialog with Close-Button """
        # otherwise circular import :(
        # pylint: disable=import-outside-toplevel
        from src_ui.setup_custom_dialog import CustomDialog
        default_title = self.dialogs["box"]["title"]
        if title is None:
            title = self.__choose_language(default_title)
        fillstring = "-" * 70
        fancy_message = f"{fillstring}\n{message}\n{fillstring}"
        messagebox = CustomDialog(fancy_message, title, self.icon_path)
        messagebox.exec_()

    def __output_language_dialog(self, options: dict, **kwargs):
        msg = self.__choose_language(options, **kwargs)
        self.standard_box(msg)

    ############################
    # Methods for creating msg #
    ############################
    def say_wrong_password(self):
        """Informs user that the password is wrong"""
        self.__output_language_dialog(self.dialogs["wrong_password"])

    def say_supply_water(self):
        """Informs user that enough water needs to be supplied for cleaning"""
        self.__output_language_dialog(self.dialogs["supply_water"])

    def say_done(self):
        """Informs user that process is done"""
        self.__output_language_dialog(self.dialogs["done"])

    def say_bottles_renewed(self):
        """Informs user that the bottles have been renewed"""
        self.__output_language_dialog(self.dialogs["bottles_renewed"])

    def say_no_recipe_selected(self):
        """Informs user that no recipe is selected"""
        self.__output_language_dialog(self.dialogs["no_recipe_selected"])

    def say_no_ingredient_selected(self):
        """Informs user that no ingredient is selected"""
        self.__output_language_dialog(self.dialogs["no_ingredient_selected"])

    def say_ingredient_still_at_bottle(self):
        """Informs user that the ingredient is still used at a bottle"""
        self.__output_language_dialog(self.dialogs["ingredient_still_at_bottle"])

    def say_ingredient_still_at_recipe(self, recipe_string: str):
        """Informs user that the ingrdient is still used in a recipe"""
        self.__output_language_dialog(self.dialogs["ingredient_still_at_recipe"], recipe_string=recipe_string)

    def say_ingredient_double_usage(self, ingredient_name: str):
        """Informs user that the ingredient is already used at least one other time"""
        self.__output_language_dialog(self.dialogs["ingredient_double_usage"], ingredient_name=ingredient_name)

    def say_ingredient_deleted(self, ingredient_name: str):
        """Informs user that the ingredient was deleted"""
        self.__output_language_dialog(self.dialogs["ingredient_deleted"], ingredient_name=ingredient_name)

    def __say_ingredient_added(self, ingredient_name: str):
        """Informs user that the ingredient was added to the database"""
        self.__output_language_dialog(self.dialogs["ingredient_added"], ingredient_name=ingredient_name)

    def __say_ingredient_changed(self, selected_ingredient: str, ingredient_name: str):
        """Informs user that the ingredient was changed"""
        self.__output_language_dialog(
            self.dialogs["ingredient_changed"],
            selected_ingredient=selected_ingredient,
            ingredient_name=ingredient_name
        )

    def say_ingredient_added_or_changed(self, ingredient_name: str, new_ingredient: bool, selected_ingredient: str = None):
        """Informs user that the ingredient was added or altered"""
        if new_ingredient:
            self.__say_ingredient_added(ingredient_name)
        else:
            self.__say_ingredient_changed(selected_ingredient, ingredient_name)

    def say_cocktail_canceled(self):
        """Informs user that the cocktail was canceled"""
        self.__output_language_dialog(self.dialogs["cocktail_canceled"])

    def say_cocktail_ready(self, comment: str):
        """Informs user that the cocktail is done with additional information what to add"""
        full_comment = ""
        if comment:
            header_comment = self.__choose_language(self.dialogs["cocktail_ready_add"])
            full_comment = f"\n\n{header_comment}{comment}"
        self.__output_language_dialog(self.dialogs["cocktail_ready"], full_comment=full_comment)

    def say_enter_cocktailname(self):
        """Informs user that no cocktailname was supplied"""
        self.__output_language_dialog(self.dialogs["enter_cocktailname"])

    def say_recipe_deleted(self, recipe_name: str):
        """Informs user that the recipe was deleted"""
        self.__output_language_dialog(self.dialogs["recipe_deleted"], recipe_name=recipe_name)

    def say_all_recipes_enabled(self):
        """Informs user that all recipes have been enabled"""
        self.__output_language_dialog(self.dialogs["all_recipes_enabled"])

    def say_recipe_added(self, recipe_name: str):
        """Informs user that the recipe was added to the database"""
        self.__output_language_dialog(self.dialogs["recipe_added"], recipe_name=recipe_name)

    def say_recipe_updated(self, old_name: str, new_name: str):
        """Informs user that the recipe was updated"""
        self.__output_language_dialog(self.dialogs["recipe_updated"], old_name=old_name, new_name=new_name)

    def say_recipe_at_least_one_ingredient(self):
        """Informs user that the recipe got no according ingredients"""
        self.__output_language_dialog(self.dialogs["recipe_at_least_one_ingredient"])

    def say_all_data_exported(self):
        """Informs user that all data have been exported"""
        self.__output_language_dialog(self.dialogs["all_data_exported"])

    def say_not_enough_ingredient_volume(self, ingredient_name: str, level: int, volume: int):
        """Informs user that the ingredient got not enough volume for cocktail"""
        level = max(0, level)
        self.__output_language_dialog(
            self.dialogs["not_enough_ingredient_volume"],
            ingredient_name=ingredient_name,
            volume=volume,
            level=level
        )

    def say_name_already_exists(self):
        """Informs user that there is already an entry in the DB with that name"""
        self.__output_language_dialog(self.dialogs["name_already_exists"])

    def say_some_value_missing(self, value: str = None):
        """Informs user that he missed at least one value"""
        if value is None:
            self.__output_language_dialog(self.dialogs["some_value_missing"])
        else:
            self.__output_language_dialog(self.dialogs["some_value_missing_specific"], value=value)

    def say_needs_to_be_int(self, value: str = None):
        """Informs user that the given value is not a number"""
        if value is None:
            self.__output_language_dialog(self.dialogs["needs_to_be_int"])
        else:
            self.__output_language_dialog(self.dialogs["needs_to_be_int_specific"], value=value)

    def say_alcohollevel_max_limit(self):
        """Informs user that the alcohol level can not be greater than 100"""
        self.__output_language_dialog(self.dialogs["alcohollevel_max_limit"])


class UiLanguage(ConfigManager):
    """Class to set the UI language to the appropriate Language"""
    cancel_button = {
        "en": "Cancel",
        "de": "Abbrechen",
    }
    enter_button = {
        "en": "Enter",
        "de": "Eintragen",
    }

    def __init__(self) -> None:
        super().__init__()
        with open(LANGUAGE_FILE, "r", encoding="UTF-8") as stream:
            self.dialogs = yaml.safe_load(stream)["ui"]

    def __choose_language(self, element: dict, **kwargs) -> Union[str, List[str]]:
        """Choose either the given language if exists, or english if not piping additional info into template"""
        language = self.UI_LANGUAGE
        tmpl = element.get(language, element["en"])
        # Return the list and not apply template!
        if isinstance(tmpl, list):
            return tmpl
        return tmpl.format(**kwargs)

    def get_add_self(self) -> str:
        """Returns add self label"""
        return self.__choose_language(self.dialogs["maker"]["add_self"])

    def get_cocktail_dummy(self) -> str:
        """Returns cocktail header dummy"""
        return self.__choose_language(self.dialogs["maker"]["cocktail_dummy"])

    def adjust_mainwindow(self, w):
        """Translates all needed elements of the main window (cocktail maker)"""
        window = self.dialogs["main_window"]
        w.PBZubereiten_custom.setText(self.__choose_language(window["prepare_button"]))
        tabs = self.__choose_language(window["tab_names"])
        for i, text in enumerate(tabs):
            w.tabWidget.setTabText(i, text)
        w.PBZeinzelnd.setText(self.__choose_language(window["single_ingredient_button"]))
        w.PBAvailable.setText(self.__choose_language(window["available_button"]))
        w.PBZaktualisieren.setText(self.__choose_language(window["change_button"]))
        w.PBZutathinzu.setText(self.__choose_language(window["add_button"]))
        w.CHBHand.setText(self.__choose_language(window["handadd_check_label"]))
        w.LIngredient.setText(self.__choose_language(window["ingredient_label"]))
        w.LAlcoholLevel.setText(self.__choose_language(window["alcohol_level_label"]))
        w.LBottleVolume.setText(self.__choose_language(window["bottle_volume_label"]))

        w.LRHandAdd.setText(self.__choose_language(window["hand_add_label"]))
        w.PBRezeptaktualisieren.setText(self.__choose_language(window["change_button"]))
        w.PBRezepthinzu.setText(self.__choose_language(window["add_button"]))

        w.PBBelegung.setText(self.__choose_language(window["change_button"]))
        w.PBFlanwenden.setText(self.__choose_language(window["renew_button"]))

    def adjust_available_windos(self, w):
        """Translates all needed elements of the available window"""
        window = self.dialogs["available_window"]
        w.PBAbbruch_2.setText(self.__choose_language(self.dialogs["cancel_button"]))
        w.LAvailable.setText(self.__choose_language(window["available_label"]))
        w.LPossible.setText(self.__choose_language(window["possible_label"]))

    def adjust_handadds_window(self, w):
        """Translates all needed elements of the handadds window"""
        window = self.dialogs["handadds_window"]
        w.PBAbbrechen.setText(self.__choose_language(self.dialogs["cancel_button"]))
        w.PBEintragen.setText(self.__choose_language(self.dialogs["enter_button"]))
        w.LHeader.setText(self.__choose_language(window["title"]))
        w.setWindowTitle(self.__choose_language(window["title"]))

    def adjust_progress_screen(self, w, cocktail_type: str):
        """Translates all needed elements of the progress window"""
        window = self.dialogs["progress_screen"]
        w.PBabbrechen.setText(self.__choose_language(self.dialogs["cancel_button"]))
        w.Labbruch.setText(self.__choose_language(window["cancel_label"]))
        w.LProgress.setText(self.__choose_language(window["progress_label"]))
        # w.LHeader.setText(self.__choose_language(window["header_label"], cocktail_type=cocktail_type))
        w.LHeader.setText(cocktail_type)

    def adjust_bonusingredient_screen(self, w):
        """Translates all needed elements of the bonusingredient window"""
        window = self.dialogs["bonusingredient_screen"]
        w.PBAbbrechen.setText(self.__choose_language(self.dialogs["cancel_button"]))
        w.PBAusgeben.setText(self.__choose_language(window["spend_button"]))
        w.LHeader.setText(self.__choose_language(window["title"]))
        w.setWindowTitle(self.__choose_language(window["title"]))

    def adjust_bottle_window(self, w):
        """Translates all needed elements of the bottle window"""
        window = self.dialogs["bottle_window"]
        w.PBAbbrechen.setText(self.__choose_language(self.dialogs["cancel_button"]))
        w.PBEintragen.setText(self.__choose_language(self.dialogs["enter_button"]))
        w.LHeader.setText(self.__choose_language(window["header"]))

    def adjust_team_window(self, w):
        """Translates all needed elements of the team window"""
        window = self.dialogs["team_window"]
        w.LHeader.setText(self.__choose_language(window["header"]))

    def generate_password_header(self, headertype: str = "password") -> str:
        """Selects the header of the passwordwindow.
        headertype: 'password', 'amount', 'alcohol'
        """
        window = self.dialogs["password_window"]
        if headertype == "password":
            return self.__choose_language(window["password"])
        if headertype == "amount":
            return self.__choose_language(window["amount"])
        if headertype == "alcohol":
            return self.__choose_language(window["alcohol"])
        raise ValueError("Currently not possible")


UI_LANGUAGE = UiLanguage()
