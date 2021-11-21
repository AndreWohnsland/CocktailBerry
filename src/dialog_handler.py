from typing import List, Union
from PyQt5.QtWidgets import QMessageBox
from config.config_manager import ConfigManager


class DialogHandler(ConfigManager):
    """Class to hold all the dialoges for the popups and language settings"""

    # def __init__(self) -> None:
    #     super().__init__()

    def __choose_language(self, element: dict) -> str:
        language = self.UI_LANGUAGE
        return element.get(language, element["en"])

    def standard_box(self, textstring):
        """ The default messagebox for the Maker. Uses a QMessageBox with OK-Button """
        messagebox = QMessageBox()
        messagebox.setStandardButtons(QMessageBox.Ok)
        buttonok = messagebox.button(QMessageBox.Ok)
        buttonok.setText("     OK     ")
        fillstring = "-" * 70
        messagebox.setText(f"{fillstring}\n{textstring}\n{fillstring}")
        messagebox.setStyleSheet(
            "QMessageBox QPushButton{background-color: rgb(0, 123, 255); color: rgb(0, 0, 0); font-size: 30pt;} QMessageBox{background-color: rgb(10, 10, 10); font-size: 16pt;} QMessageBox QLabel{color: rgb(0, 123, 255);}"
        )
        messagebox.showFullScreen()
        messagebox.exec_()

    def __output_language_dialog(self, options: dict):
        msg = self.__choose_language(options)
        self.standard_box(msg)

    ############################
    # Methods for creating msg #
    ############################
    def say_wrong_password(self):
        options = {
            "en": "Wrong Password!",
            "de": "Falsches Passwort!",
        }
        self.__output_language_dialog(options)

    def say_supply_water(self):
        options = {
            "en": "Machine will be cleaned, please provide enough water. OK to continue.",
            "de": "Maschine wird gereinigt, genug Wasser bereitstellen! OK zum Fortfahren.",
        }
        self.__output_language_dialog(options)

    def say_done(self):
        options = {
            "en": "Done!",
            "de": "Fertig!",
        }
        self.__output_language_dialog(options)

    def say_bottles_renewed(self):
        options = {
            "en": "Renewed selected bottles!",
            "de": "Ausgewählte Flaschen erneuert!",
        }
        self.__output_language_dialog(options)

    def say_no_recipe_selected(self):
        options = {
            "en": "No recipe selected!",
            "de": "Kein Rezept ausgewählt!",
        }
        self.__output_language_dialog(options)

    def say_no_ingredient_selected(self):
        options = {
            "en": "No ingredient selected!",
            "de": "Keine Zutat ausgewählt!",
        }
        self.__output_language_dialog(options)

    def say_ingredient_still_at_bottle(self):
        options = {
            "en": "Error, the ingredient is still used at a bottle!",
            "de": "Fehler, die Zutat ist noch in der Belegung registriert!",
        }
        self.__output_language_dialog(options)

    def say_ingredient_still_at_recipe(self, recipe_string: str):
        options = {
            "en": f"Recipe can't be deleted, it is still used at:\n<{recipe_string}>",
            "de": f"Zutat kann nicht gelöscht werden, da sie in:\n<{recipe_string}>\ngenutzt wird!",
        }
        self.__output_language_dialog(options)

    def say_ingredient_double_usage(self, ingredient_name: str):
        options = {
            "en": f"One of the ingredient\n<{ingredient_name}>\nwas used multiple times!",
            "de": f"Eine der Zutaten:\n<{ingredient_name}>\nwurde doppelt verwendet!",
        }
        self.__output_language_dialog(options)

    def say_ingredient_deleted(self, ingredient_name: str):
        options = {
            "en": f"Ingredient:\n<{ingredient_name}>\ndeleted",
            "de": f"Zutat mit dem Namen:\n<{ingredient_name}>\ngelöscht!",
        }
        self.__output_language_dialog(options)

    def __say_ingredient_added(self, ingredient_name: str):
        options = {
            "en": f"Ingredient\n<{ingredient_name}>\nentered",
            "de": f"Zutat mit dem Namen:\n<{ingredient_name}>\neingetragen",
        }
        self.__output_language_dialog(options)

    def __say_ingredient_changed(self, selected_ingredient: str, ingredient_name: str):
        options = {
            "en": f"Ingredient\n<{selected_ingredient}>\nwas updated to\n<{ingredient_name}>",
            "de": f"Zutat mit dem Namen:\n<{selected_ingredient}>\nunter\n<{ingredient_name}>\naktualisiert",
        }
        self.__output_language_dialog(options)

    def say_ingredient_added_or_changed(self, ingredient_name: str, new_ingredient: bool, selected_ingredient: str = None):
        if new_ingredient:
            self.__say_ingredient_added(ingredient_name)
        else:
            self.__say_ingredient_changed(selected_ingredient, ingredient_name)

    def say_cocktail_canceled(self):
        options = {
            "en": "The cocktail was cancelled!",
            "de": "Der Cocktail wurde abgebrochen!",
        }
        self.__output_language_dialog(options)

    def say_cocktail_ready(self, comment: str):
        options_comment = {
            "en": "Also add:",
            "de": "Noch hinzufügen:",
        }
        full_comment = ""
        if comment:
            header_comment = self.__choose_language(options_comment)
            full_comment = f"\n\n{header_comment}{comment}"
        options = {
            "en": f"The cocktail is ready. Please wait a moment, for the rest of the fluid to flow in.{full_comment}",
            "de": f"Der Cocktail ist fertig! Bitte kurz warten, falls noch etwas nachtropft.{full_comment}",
        }
        self.__output_language_dialog(options)

    def say_enter_cocktailname(self):
        options = {
            "en": "Please enter cocktail name!",
            "de": "Bitte Cocktailnamen eingeben!",
        }
        self.__output_language_dialog(options)

    def say_recipe_deleted(self, recipe_name: str):
        options = {
            "en": f"Recipe\n<{recipe_name}>\nwas deleted",
            "de": f"Rezept mit dem Namen\n<{recipe_name}>\nwurde gelöscht!",
        }
        self.__output_language_dialog(options)

    def say_all_recipes_enabled(self):
        options = {
            "en": "All recipes are set to active!",
            "de": "Alle Rezepte wurden wieder aktiv gesetzt!",
        }
        self.__output_language_dialog(options)

    def say_recipe_added(self, recipe_name: str):
        options = {
            "en": f"Recipe\n<{recipe_name}>\nwas added!",
            "de": f"Rezept unter dem Namen:\n<{recipe_name}>\neingetragen!",
        }
        self.__output_language_dialog(options)

    def say_recipe_updated(self, old_name: str, new_name: str):
        options = {
            "en": f"Recipe\n<{old_name}>\nupdated to\n<{new_name}>",
            "de": f"Rezept mit dem Namen:\n<{old_name}>\nunter dem Namen:\n<{new_name}>\naktualisiert!",
        }
        self.__output_language_dialog(options)

    def say_recipe_at_least_one_ingredient(self):
        options = {
            "en": "You need to use at least one ingredient!",
            "de": "Es muss mindestens eine Zutat eingetragen sein!",
        }
        self.__output_language_dialog(options)

    def say_all_data_exported(self):
        options = {
            "en": "All data was exported and amount was reset!",
            "de": "Alle Daten wurden exportiert und die zurücksetzbaren Mengen zurückgesetzt!",
        }
        self.__output_language_dialog(options)

    def say_not_enough_ingredient_volume(self, ingredient_name: str, level: int, volume: int):
        options = {
            "en": f"{ingredient_name} has not enough volume! {volume} ml is needed, only {level} ml left.",
            "de": f"{ingredient_name} hat nicht genug Volumen! {volume} ml benötigt aber nur {level} ml vorhanden.",
        }
        self.__output_language_dialog(options)

    def say_name_already_exists(self):
        options = {
            "en": "This name is already used!",
            "de": "Dieser Name wurde bereits verwendet!",
        }
        self.__output_language_dialog(options)

    def say_some_value_missing(self, value: str = None):
        options_default = {
            "en": "At least one value is missing!",
            "de": "Irgendwo ist ein Wert vergessen worden!",
        }
        options_specific = {
            "en": f"{value} is missing!",
            "de": f"{value} wurde vergessen!",
        }
        if value is None:
            self.__output_language_dialog(options_default)
        else:
            self.__output_language_dialog(options_specific)

    def say_needs_to_be_int(self, value: str = None):
        options_default = {
            "en": "Wrong value for a number field!",
            "de": "Falscher Wert für ein Zahlenfeld!",
        }
        options_specific = {
            "en": f"{value} needs to be a number!",
            "de": f"{value} muss eine ganze Zahl sein!",
        }
        if value is None:
            self.__output_language_dialog(options_default)
        else:
            self.__output_language_dialog(options_specific)

    def say_alcohollevel_max_limit(self):
        options = {
            "en": "Alcohol level can't exceed 100 percent!",
            "de": "Alkoholgehalt kann nicht größer als 100 Prozent sein!",
        }
        self.__output_language_dialog(options)


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

    def __choose_language(self, element: dict) -> Union[str, List[str]]:
        language = self.UI_LANGUAGE
        return element.get(language, element["en"])

    def get_add_self(self) -> str:
        options = {
            "en": "Add by hand:",
            "de": "Selbst hinzufügen:"
        }
        return self.__choose_language(options)

    def get_volume_for_dynamic(self, value: int) -> str:
        options = {
            "en": f"Volume: {value} ml",
            "de": f"Menge: {value} ml",
        }
        return self.__choose_language(options)

    def get_volpc_for_dynamic(self, value: float) -> str:
        options = {
            "en": f"{value:.0f}% alcohol",
            "de": f"{value:.0f}% Alkohol",
        }
        return self.__choose_language(options)

    def adjust_mainwindow(self, w):
        prepare_button = {
            "en": "Prepare",
            "de": "Zubereiten",
        }
        tab_names = {
            "en": ["Maker", "Ingredients", "Recipes", "Bottles"],
            "de": ["Maker", "Zutaten", "Rezepte", "Flaschen"],
        }
        ingredient_label = {
            "en": "Ingredient",
            "de": "Zutat",
        }
        alcohol_level_label = {
            "en": "Alcohol (in %)",
            "de": "Alkoholgehalt (in %)",
        }
        bottle_volume_label = {
            "en": "Bottle Volume (ml)",
            "de": "Flaschenvolumen (ml)",
        }
        single_ingredient_button = {
            "en": "Spend single ingredient",
            "de": "Einzelne Zutat Ausgeben",
        }
        handadd_check_label = {
            "en": "Only add self by hand",
            "de": "Nur selbst hinzufügen",
        }
        available_button = {
            "en": "available",
            "de": "verfügbar",
        }
        change_button = {
            "en": "change",
            "de": "ändern",
        }
        add_button = {
            "en": "add",
            "de": "hinzufügen",
        }
        hand_add_label = {
            "en": "Add self by hand:",
            "de": "Selbst hinzufügen:",
        }
        renew_button = {
            "en": "apply new bottles",
            "de": "neue Flaschen anwenden",
        }
        w.PBZubereiten_custom.setText(self.__choose_language(prepare_button))  # Zubereiten
        tabs = self.__choose_language(tab_names)
        for i, text in enumerate(tabs):
            w.tabWidget.setTabText(i, text)
        w.PBZeinzelnd.setText(self.__choose_language(single_ingredient_button))
        w.PBAvailable.setText(self.__choose_language(available_button))
        w.PBZaktualisieren.setText(self.__choose_language(change_button))
        w.PBZutathinzu.setText(self.__choose_language(add_button))
        w.CHBHand.setText(self.__choose_language(handadd_check_label))
        w.LIngredient.setText(self.__choose_language(ingredient_label))
        w.LAlcoholLevel.setText(self.__choose_language(alcohol_level_label))
        w.LBottleVolume.setText(self.__choose_language(bottle_volume_label))

        w.LRHandAdd.setText(self.__choose_language(hand_add_label))
        w.PBRezeptaktualisieren.setText(self.__choose_language(change_button))
        w.PBRezepthinzu.setText(self.__choose_language(add_button))

        w.PBBelegung.setText(self.__choose_language(change_button))
        w.PBFlanwenden.setText(self.__choose_language(renew_button))

    def adjust_available_windos(self, w):
        available_label = {
            "en": "Available",
            "de": "Vorhanden",
        }
        possible_label = {
            "en": "Possible",
            "de": "Möglich",
        }
        w.PBAbbruch_2.setText(self.__choose_language(self.cancel_button))
        w.LAvailable.setText(self.__choose_language(available_label))
        w.LPossible.setText(self.__choose_language(possible_label))

    def adjust_handadds_window(self, w):
        title = {
            "en": "Ingredients for hand add",
            "de": "Zutaten zum selbst hinzufügen",
        }
        w.PBAbbrechen.setText(self.__choose_language(self.cancel_button))
        w.PBEintragen.setText(self.__choose_language(self.enter_button))
        w.setWindowTitle(self.__choose_language(title))

    def adjust_progress_screen(self, w, cocktail_type: str):
        cancel_label = {
            "en": "The Cocktail can also be canceled",
            "de": "Der Vorgang kann auch abgebrochen werden",
        }
        progress_label = {
            "en": "Progress:",
            "de": "Fortschritt:",
        }
        header_label = {
            "en": f"{cocktail_type} is being prepared!",
            "de": f"{cocktail_type} wird zubereitet!",
        }
        w.PBabbrechen.setText(self.__choose_language(self.cancel_button))
        w.Labbruch.setText(self.__choose_language(cancel_label))
        w.LProgress.setText(self.__choose_language(progress_label))
        w.Lheader.setText(self.__choose_language(header_label))

    def adjust_bonusingredient_screen(self, w):
        spend_button = {
            "en": "Spend",
            "de": "Ausgeben",
        }
        title = {
            "en": "Select output ingredient",
            "de": "Zutatenausgabe auswählen",
        }
        w.PBAbbrechen.setText(self.__choose_language(self.cancel_button))
        w.PBAusgeben.setText(self.__choose_language(spend_button))
        w.setWindowTitle(self.__choose_language(title))

    def adjust_bottle_window(self, w):
        header = {
            "en": "Select/change level of bottles",
            "de": "Füllstand der Flaschen auswählen/ändern",
        }
        w.PBAbbrechen.setText(self.__choose_language(self.cancel_button))
        w.PBEintragen.setText(self.__choose_language(self.enter_button))
        w.LHeader.setText(self.__choose_language(header))

    def adjust_team_window(self, w):
        header = {
            "en": "Select your Team",
            "de": "Team auswählen",
        }
        w.Lheader.setText(self.__choose_language(header))

    def generate_password_header(self, headertype: str = "password") -> str:
        """Selects the header of the passwordwindow.
        headertype: 'password', 'amount', 'alcohol'
        """
        password = {
            "en": "Please enter password!",
            "de": "Bitte Passwort eingeben!",
        }
        amount = {
            "en": "Please enter amount!",
            "de": "Bitte Menge eingeben!",
        }
        alcohol = {
            "en": "Please enter alcohol!",
            "de": "Bitte Alkoholgehalt eingeben!",
        }
        if headertype == "password":
            return self.__choose_language(password)
        if headertype == "amount":
            return self.__choose_language(amount)
        if headertype == "alcohol":
            return self.__choose_language(alcohol)
        raise ValueError("Currently not possible")


UI_LANGUAGE = UiLanguage()
