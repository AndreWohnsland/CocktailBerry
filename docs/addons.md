# Addons

Addons are third party extensions which add additional features to CocktailBerry.
Currently, addons can be triggered at:

- At the start of the program
- Just before the program exits
- Before a cocktail is prepared, this may also prevent the cocktail
- After a cocktail is prepared
- Build up it's own GUI or buttons to execute other program logic

You can use the addons to implement some exotic feature, just for you, or make it accessible for the public.
Addons were introduced to give the user more control over specific things.
Like you could implement a scale into your machine below the position for the glass and only prepare the cocktail if a glass is recognized.

!!! danger "Everyone can make Addons"
    In general, you should check and understand the addon or trust the author of it.
    Addons are not made directly by the CocktailBerry development team.
    The installation of additional packages required for the addon must also be handled be the user or the provided addon.
    Usually, the addon provider should deliver an installation or setup guide for the addon.

The extension for addons was made, so that there is not big feature creep within the main application.
This would cause more and more optional settings, which most user are not interested in.
With addons users will get the best base experience with CocktailBerry, but can easy extent it to their own taste.

Some examples for an addon could be:

- Implementation of a weight scale to detect if a glass is present
- Add a checklist for invoices or cost splitting
- Modify starting values (default output volume, eg.) to let them be changed over the GUI
- Integrate external things like automatic ice crasher
- And almost anything you can think of

## Installing Addons

There are two options to install an addon.
If it's an [official addon](https://github.com/AndreWohnsland/CocktailBerry-Addons), you can manage it over CocktailBerry.
Go to Setting > Addons > Manage, there you can check the addons you want to have installed.
For any none official one, just put the Python file of the addon into the `addons` folder.
It is usually located at `~/CocktailBerry/addons`.
If the addon needs additional Python packages, make sure you also install the needed requirements by the addon.
An addon should only contain **one** file per addon.
If an addon is not working properly, this is mostly due to an error within the addon and not CocktailBerry.
If you think it is related to CocktailBerry, you can open an according issue.

## Updating Addons

The update process is quite similar to the installation one.
Either go to the CocktailBerry GUI for addons, manage and apply the addons.
This will also update existing ones.
If you use an external one, just replace the current file with the latest one, this let you run the latest version.

## Verified Addons

Here is a list of verified addons that you can use.
They are either directly from CocktailBerry or from other third party providers.
Verifies means that the addon is known by the CocktailBerry programmers and was at least once tested for its functionality.

- [Start Glass Volume](https://github.com/AndreWohnsland/CocktailBerry-Addons#start-glass-volume): Change default glass volume at machine start
- It's a new feature, so let's make some addons!

!!! question "Not the Addon you're Looking for?"
    Not all addons may be listed here.
    This is either because not all people will show their addons, or they are currently not known.
    If you created a cool one, contact CocktailBerry!
    Also, it's quite easy to get started, so you might want to build your own perfect fit.
    If you want to contribute, also have a look into the [Addons Repo](https://github.com/AndreWohnsland/CocktailBerry-Addons).

## Creating Addons

This section is for people, who want to write your own addons. 
Here you will find the ressources to get started.

!!! info "Developers Guide"
    This section is for developer and people, who want to add some features to CocktailBerry.
    If you just want to use addons of other people, look at the sections above.

### Set Up

First, you should clone the latest version of CocktailBerry in your development environment.
Install all needed dependencies, either over pip or with poetry (recommended).
Usually **one** Python file is used per addon, placed in the `addons` folder in the CocktailBerry project.
Files within this folder will not be tracked by git.

!!! tip "Use the CLI"
    It's super easy to create a skeleton addon file with the [CLI command](commands.md#creating-addon-base-file)!
    Just run: 
    
    ```bash
    python runme.py create-addon "Your Addon Name"
    ```

    This will create a file with the needed structure in the addons folder.

And you are ready to go.

### Addon Base Structure

An addon can currently execute code at init, cleanup, start or end of a cocktail.
In addition, you can provide logic to build up your own GUI, if it is necessary.
The file needs the Addon class, please also inherit from the Interface, so you get information about all functions.
A more detailed description can be found at the plus icons in the code below.
Even if not all functions must be present within the file, it is best practice to define all.
So it is explicitly clear, that some of the functions do not do anything by design.
A basic structure could look like this:

```python
from src.programs.addons import AddonInterface # (1)!

ADDON_NAME = "Your Displayed Name"

class Addon(AddonInterface): # (2)!
    def setup(self): # (3)!
        pass

    def cleanup(self): # (4)!
        pass

    def before_cocktail(self, data: dict): # (5)!
        pass

    def after_cocktail(self, data: dict): # (6)!
        pass

    def build_gui(
        self,
        container,
        button_generator
    ) -> bool: # (7)!
        return False
```

1. Using the `AddonInterface` will give you intellisense for the existing functions available. 
2. Your class needs to have the name Addon and should inherit from the AddonInterface.
3. Initializes the addon, executed at program start.
4. Method for cleanup, executed a program end just before the program closes.
5. Executed right before the cocktail preparation. In case of a RuntimeError, the cocktail will not be prepared and the message will be shown to the user instead.
6. Executed right after the cocktail preparation, before other services are connected or DB is updated.
7. Will be used if the user navigates to the addon window and selects your addon. The container is a PyQt5 Layout widget you can (but not must) use to define custom GUI elements and connect them to functions. If you just want to have buttons executing functions, you can use the button generator function. Return False, if not implemented.

Now that you know the skeleton, you can fill it with your program logic.

### Defining Addon Configurations

Some addons may need additional user information, like connected pins, or other variable settings.
The easiest (but bad) way is to hard code this into the code and let the user change this value.
But this approach is not robust against code changes (new versions of addon), and also not user friendly (config not accessible over GUI).
Therefore, the addon provider can use the CocktailBerry configuration.
To do so, the user needs to inject the config name, type and validation function into the config.
There is also the option to provided a description, as well as according translations.
You can find each direction in the subsections below.

#### Add Config Values

To add additional configuration you need to import the `CONFIG` object and add your config to it.
Please take note that the config will hold all existing values in the file, so try not to use a name that already exists in the base CocktailBerry config.
You can either run the config setting at module level, or within the init() function.
The latter is recommended and usually more appropriate, but this may depend on your program logic.
Currently supported types are int, float, str, list, bool and [ChooseType](#using-selection-for-dropdowns).
The type is used to define the input dialog within the settings GUI.
It is strongly recommended to give your config value the prefix `ADDON_` to distinguish it from the base program settings.
Also use an appropriate, not too long name, as well as all capital letters and underscores as word separator (*screaming snake case*).
You can have a look at the other values as a reference.

```python
from src.config_manager import CONFIG as cfg # (1)!

def setup(self):
    cfg.add_config("ADDON_CONFIG", "DefaultValue") # (2)!
```

1.  Needs to import the `CONFIG` object from CocktailBerry.
2.  Adds the configuration under given name and default value. Currently supported are int, float, str, bool and list. Different types have different input mask in the config GUI.

#### Use Config Values

Using existing, as well as your newly defined configuration values is quite easy.
All configuration are stored within the `CONFIG` object and are accessible there.
You can use the config name as its attribute to get the desired configuration.

```python
my_config = cfg.ADDON_CONFIG # (1)!
my_config = getattr(cfg, "ADDON_CONFIG") # (2)!
program_language = cfg.UI_LANGUAGE # (3)!
```

1. You can access your previously defined attributes over the `CONFIG` object.
2. Using the `getattr()` will work as well, if you prefer this way.
3. The `CONFIG` object also holds all settings, which are in the base CocktailBerry app. You can access them as well!

#### Add Validation

You can further add validation besides the type validation of your config.
If you don't want to have any other validation besides the type, you don't need to provide additional information.
If you want to have additional validation, you can pass any number of functions into the validation list.
Each function needs to have two arguments: The first one being the config name, the second one is the according value.
If the value is not valid, you must raise a ConfigError, other errors are not caught by the GUI.
The description of the error should inform the user, why it is not valid.
Cases may be limiting length of characters, only specific number ranges or similar.

```python
from src.config_manager import ConfigError # (1)!

def _check_function(configname: str, configvalue: str): # (2)!
    if configvalue == "forbidden": # (3)!
        raise ConfigError( # (4)!
            f"The value {configvalue} for {configname} is not allowed."
        )

def setup(self):
    cfg.add_config(
        "ADDON_CONFIG",
        "DefaultValue",
        [_check_function]
    ) # (5)!
```

1. Please use the `ConfigError` class from CocktailBerry.
2. Check function for config validation. First argument is the configname, second is the configvalue.
3. We just raise the exception if the value is "forbidden".
4. Failed validation should throw the `ConfigError`, other errors will crash the app.
5. You can define any number of check function. Please take care that the function interface has two arguments.

#### Validate List Settings

An extra case is, if your setting is a list of values.
In this case, you can also add a validation function, which will validate each list element.
The schema is identical as before, you can define your custom validation functions.
Take note that currently no nested lists are supported and each list element needs to have the same type.
If the default value is an empty list, you must provide the element type to the `list_type` argument.
Otherwise, the string type will used as fallback type.

```python
def _less_than_10(configname: str, configvalue: int): # (1)!
    if configvalue > 10:
        raise ConfigError(
            f"The value for {configname} needs to be less than 10."
        )

def setup(self):
    cfg.add_config( # (2)!
        "ADDON_LIST",
        [1, 2, 3],
        [], # (3)!
        [_less_than_10] # (4)!
    ) 
```

1. This function just raises an error is the value is 10 or greater. Again, use the ConfigError, as shown in the last example.
2. The general set up is identical to the other config examples.
3. Here you could check the list, for example if the length meets a criteria. We do not check anything additional.
4. Here you can check each element in the list, in this case we check if any element is >10.

#### Using Selection for Dropdowns

You may want to offer only a selection of values to the user.
In this case, you provide a list of allowed string values.
The default value will be the first element of the options, but you can also define this value, if it should be another one.
The GUI will then display a drop down, only showing the allowed values.
Please take note, if you want types other than string, you need to convert them after you retrieve the value from the config.
The dropdown element only support string values.


```python
def setup(self):
    options = ["List", "of", "allowed", "values"] # (1)!
    cfg.add_selection_config(
        "ADDON_SELECTION",
        options,
        options[1], # (2)!
    )

    cfg.add_selection_config(
        "ADDON_SELECTION_INT",
        ["10", "25", "50"] # (3)!
    )
    none_string_value = int(cfg.ADDON_SELECTION_INT) # (4)!

```

1. First, you need to define the list of allowed options.
2. Here, you set the default value to the second option. The default value uses the first option.
3. Provide the values as string, even if they are other (here int) types
4. Convert the values after retrieving to your desired type

#### Add GUI Description

Optionally, you can add an additional description to your configuration.
This helps users using the GUI understanding the value better.
Use the `UI_LANGUAGE` object to set the configuration description.
You can either use a single string describing the config in english, or use a dictionary with the language codes.
At least english is needed, if you do not provided a full list of translations.
If you don't want to provide GUI description, you can skip this step.
But it is encouraged to do so to improve user experience.

```python
from src.dialog_handler import UI_LANGUAGE as uil # (1)!

def setup(self):
    ...
    desc = {
        "en": "English description",
        "de": "Deutsche Beschreibung",
    } # (2)!
    uil.add_config_description("ADDON_CONFIG", desc)

    desc2 = "Just an english description" # (3)!
    uil.add_config_description("ADDON_CONFIG2", desc2)

```

1. You need to import the `UI_LANGUAGE` object to access the dialogues
2. If you do provide a dictionary, it needs at least the english (`en`) key!
3. You can also just use a string in the english language, if you don't want to provide translation 

### Prevent Cocktail Preparation

Your addon may want to check some condition before cocktail preparation.
This way, you can prevent the preparation of the cocktail.
For example, if your scale does not recognize a glass, a cocktail should not be prepared.
To break the preparation process, raise a RuntimeError. 
Please do not use other error types, because only this type will be caught and handled.
You can provide an error message in either english, or an according translation for the current language.
You do not need to provide all languages if you do an translation, but you need at least the english one.
The error message will be shown as a dialog to the user, so it should explain why the cocktail was not prepared.

```python
def before_cocktail(self, data: dict):
    everything_ok = your_custom_check_logic() # (1)!
    msg = {
        "en": "No glass was detected!",
        "de": "Kein Glas wurde erkannt!",
    } # (2)!

    if not everything_ok:
        message = msg.get(cfg.UI_LANGUAGE, msg["en"]) # (3)!
        raise RuntimeError(message) # (4)!
```

1. Insert your custom logic to check on condition or external devices if everything is as it should be.
2. You can either directly provide the message, or again define a translation. In the latter, see handling below. If you do provide translation, please make sure english is at least present.
3. When you do the language selection here, it is best to fall back to `en` on a not found key. This is useful when a new language is released, which your addon currently does not support. Otherwise a KeyError will crash the program. The current language is in `cfg.UI_LANGUAGE`.
4. Please raise a `RuntimeError`, other errors will not be caught and crash the program. The used message will be shown to the user.

### Using the Logger

The best way to implement logging into your addon is to use the internal CocktailBerry logger.
This way, your logs are saved and formatted the same way as the other logs.
This makes it easy for the user to view them over the GUI.
The `log_event` takes two arguments: The log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL") and the log message.
Or you can just use the default way, the python logger is implemented with the according level function.

```python
from src.logger_handler import LoggerHandler # (1)!
_logger = LoggerHandler("ADDON: Name") # (2)!

def setup(self):
  _logger.log_event(
    "INFO",
    "ADDON NAME has been initialized successfully"
  ) # (3)!
  _logger.debug("This works as well") # (4)!
```

1. Import the `LoggerHandler` from CocktailBerry to set up your logger.
2. Give the logger a name, it will be shown in the logs to pinpoint the messages. As a suggestion: use *ADDON: YourName* as the logger name, so it's clear the message comes from an addon.
3. The logger uses the base python logger in the background but delivers an abstraction. Levels are "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
4. You can also use the known debug, info, warning, error and critical functions to log your message

### Accessing Default Database

There are scenarios where you want to persistently store your data.
You can either define your own database location and use a framework to your liking, or use the default CocktailBerry database.
If you want to use the default database, import the `DB_COMMANDER` object.
The handler attribute have the `query_database` command as an abstraction to interact with the database.
Here you can execute SQLite commands passed as a string.
If you want to have dynamic arguments, you can pass them according to the SQLite syntax (`?`), with the corresponding values in the second argument as tuple.
The results are automatically fetched and returned as a list of tuples.
Changes are automatically committed by the handler.
Please take note that you need to create your table if it does not exist.

```python
from src.database_commander import DB_COMMANDER as dbc # (1)!

def setup(self):
    dbc.handler.query_database(
        "CREATE TABLE IF NOT EXISTS YourTable(...)"
    ) # (2)!
    ...
    result = dbc.handler.query_database(
        "SELECT * FROM YourTable"
    ) # (3)!
    
    filter_value = 10
    result = dbc.handler.query_database(
        "SELECT * FROM YourTable WHERE Column=?",
        (filter_value,)
    ) # (4)!
```

1. Import the `DB_COMMANDER` from CocktailBerry to use the default database.
2. Ensure that your table exists, so creating it at initialization is a good practice.
3. The `handler` object can call the `query_database` command. This uses the SQLite syntax. Results are fetched and returned as list of tuples. Changes are committed after the execution, so no need for a `.commit()`.
4. If you want to provide dynamic values, you can use the question mark `?` in the query and pass the value along with the second argument in a tuple.

### Own GUI

The `build_gui()` function is used to build up an own GUI for your addon if the user navigates to the addon window.
A `container` (QVBoxLayout) for your elements is provided, where you can fill in custom Qt elements, if you want that.
If you just want to have some buttons which executes a function, when the user clicks on it, you can use the `button_generator`.
It takes a string (label of the button) and a function (executed at button click) as arguments.
With the help of this function, you can generate Qt buttons without knowing any Qt at all.
If you are experienced with Qt, you can use the container to build more complex things.

```python
from typing import Callable

def _button_function():  # (1)!
    print("The button was clicked")

def build_gui(
    self,
    container,
    button_generator: Callable[[str, Callable], None], # (2)!
) -> bool:
    button_generator("click me", _button_function) # (3)!
    return True # (4)!
```

1. We just define a very simple function, which prints some text to the console.
2. Type hints make your life, as well as autocompletion of your IDE easier.
3. We generate a button with the label "click me" and pass our function. The function will be executed on button click.
4. Return True if you provide build up logic. Otherwise the GUI will inform the user, that the addon does not provide any GUI.

A more sophisticated example here uses the container object to add some text and a line edit to the GUI.

```python
from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QLabel

def build_gui(
    self,
    container: QVBoxLayout, # (1)!
    button_generator
):
    my_label = container.addWidget(QLabel("Some Label text")) # (2)!
    my_line_edit = container.addWidget(QLineEdit("")) # (3)!
    return True
```

1. Again, type hints make your life easier.
2. Here we just create a simple label.
3. You can create any Qt element you want and also use them in your program logic, for example the button press.

If you want to have a different name from your file name displayed in the addon selection, you can define the `ADDON_NAME` in your file.

```python
ADDON_NAME = "Your Displayed Name" # (1)!
```

1. Define the ADDON_NAME at root level (outside the other functions or classes) in your file.

### Dialogues an Prompts

There are times, you either want to inform the user with a dialog or want to have a confirmation of the user.
In this cases, you can use the `DP_CONTROLLER` object.
The method `standard_box` will create a window showing your text.
The method `user_ok` will prompt the user with the text and return if the user pressed ok.
Those methods will use the default used elements from CocktailBerry.

```python
from src.display_controller import DP_CONTROLLER as dpc # (1)!

def after_cocktail(self, data: dict):
    if dpc.user_okay("Should I do it?"): # (2)!
        dpc.standard_box("I will do it") # (3)!
```

1. Import the `DP_CONTROLLER` from CocktailBerry to use dialogues.
2. The `user_okay` method will wait until the user accepts or decline and return the result as boolean.
3. The `standard_box` will display your text as a full screen window, with a close / ok button.


### Data Before and After Cocktail

In addition for the action before and after the cocktail preparation, there is additional data provided with the function.
You can use the data for your custom logic.
All data is contained within the dictionary as first argument.
You can extract the needed properties from it.
In the future, there may be more attributes you can use.
The advantage of an dictionary is that this won't break your addon, if new properties are added.

#### Before Cocktail

Following attributes are available in the before_cocktail data:

- cocktail: Cocktail object, containing name, adjusted_ingredients and many more attributes. Ingredient object got name and amount for example.

#### After Cocktail

Following attributes are available in the after_cocktail data:

- cocktail: Cocktail object, containing name, adjusted_ingredients and many more attributes. Ingredient object got name and amount for example.
- consumption: List of spend ingredients, which where added by machine (cocktail.machineadds).

### And Many More

In theory, you can use any element from CocktailBerry, but this would go beyond the scope and is not necessary in most cases.
If you are a little familiar with the base code, this should no problem for you.
Some examples may be:

- `src.machine.rfid` RFID Controller
- `src.machine.leds` LED Controller

### Provide Documentation

If your addon uses other external dependencies (Python libraries), please provide some sort of installation guide.
The easiest way would be information in the readme of your project, that instructs the user which commands are necessary to get the addon running.
Also, if your configuration values are more complex or do need additional context, it is best practice to also provide documentation for them.
This will reduce user confusion an will raise the popularity of your addon.

If you created a cool addon, you can link me the project.
It may be included here, after it's functionality has been verified.
This way, more users may find the addon and can use it.

### Make it Verified

To publish your addon and make it visible to the users of CocktailBerry, you can checkout the [official repository](https://github.com/AndreWohnsland/CocktailBerry-Addons).
CocktailBerry will use the information listed there, to get the addon data.
Follow the development steps to make your addon a verified and accessible addon!