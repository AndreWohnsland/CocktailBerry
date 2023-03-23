# Addons

Addons are third party extensions which may add additional features to CocktailBerry.
Currently, addons can be triggered at:

- `init`: At the start of the machine
- `cleanup`: Just before the program exits
- `start`: Before a cocktail is prepared, this may also prevent the cocktail
- `end`: After a cocktail is prepared

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

## Installing Addons

To install an addon, just put the Python file of the addon into the `addons` folder.
It is usually located at `~/CocktailBerry/addons`.
If the addon needs additional Python packages, make sure you also install the needed requirements by the addon.
An addon should only contain **one** file per addon.
If an addon is not working properly, this is mostly due to an error within the addon and not CocktailBerry.
If you think it is related to CocktailBerry, you can open an according issue.

## Verified Addons

Here is a list of verified addons that you can use.
They are either directly from CocktailBerry or from other third party providers.
Verifies means that the addon is known by the CocktailBerry programmers and was at least once tested for its functionality.

- It's a new feature, so let's make some addons!

!!! question "Not the Addon you're Looking for?"
    Not all addons may be listed here.
    This is either because not all people will show their addons, or they are currently not known.
    If you created a cool one, contact CocktailBerry!
    Also, it's quite easy to get started, so you might want to build your own perfect fit.

## Creating Addons

This section is for people, who want to write your own addons. 
Here you will find the ressources to get started.

### Set Up

First, you should clone the latest version of CocktailBerry in your development environment.
Files within this folder will not be tracked by git.
Install all needed dependencies, either over pip or with poetry (recommended).
Then you should create **one** Python file for your addon, placed in the `addons` in the CocktailBerry project folder.
Now you are ready to go.

### Addon Base Structure

An addon can currently execute code at init, cleanup, start or end of a cocktail.
A more detailed description can be found at the plus icons in the code here.
Even if not all functions must be present within the file, it is best practice to define all.
So it is explicitly clear, that some of the functions do not do anything by design.
A basic structure could look like this:

```python
def init(): # (1)!
    pass

def cleanup(): # (2)!
    pass

def start(): # (3)!
    pass

def end(): # (4)!
    pass

```

1. Initializes the addon, executed at program start, at the end of the mainwindow setup.
2. Method for cleanup, executed a program end just before the program closes.
3. Executed right before the cocktail preparation. In case of a RuntimeError, the cocktail will not be prepared and the message will be shown to the user instead.
4. Executed right after the cocktail preparation, before other services are connected or DB is updated.

Now, your addon got the skeleton you can fill with your program logic.

### Defining Addon Configurations

Some addons may need additional user information, like connected pins, or other variable settings.
The easiest (but bad) way is to hard code this into the code and let the user change this value.
But this approach is not robust against code changes (new versions of addon), and also not user friendly (config not accessible over GUI).
Therefore, the addon provider can use the CocktailBerry configuration.
To do so, the user needs to inject the config name, type and validation function into the config.
There is also the option to provided a description, as well as according translations.
You can find each direction in the subsections below.

#### Add Config Value

To add additional configuration you need to import the `CONFIG` object and add your config to it.
Please take note that the config will hold all existing values in the file, so only assign the default value if it does not exist.
This is usually the case if a user has just added the addon and the program was not started since then.
You can either run the config setting at module level, or within the init() function.
The latter is recommended and usually more appropriate, but this may depend on your program logic.
In addition, you need to define at least the type of your config value in the `config_type` dictionary.
Currently supported types are int, float, str, list, and [ChooseType](#using-selection-for-dropdown).
The type is used to define the input dialog within the settings GUI.
Other types will programmatically work, but the input mask will be using a line edit with the usual keyboard layout in the GUI.
It is strongly recommended to give your config value the prefix `ADDON_` to distinguish it from the base program settings.
Also use an appropriate, not too long name, as well as all capital letters and underscores as word separator (screaming snake case).
You can have a look at the other values as a reference.

```python
from src.config_manager import CONFIG as cfg # (1)!

def init():
    if not hasattr(cfg, 'ADDON_CONFIG'): # (2)!
        cfg.ADDON_CONFIG = "DefaultValue"  # type: ignore
    cfg.config_type["ADDON_CONFIG"] = (str, []) # (3)!
```

1.  Needs to import the `CONFIG` object from CocktailBerry.
2.  Basic config integration, used at init(), adds addon default configuration into the config object if it does not exists.
3.  Also need to add the type to the config. The type needs to be defined, that the GUI will work. Currently supported are int, float, str, list, and ChooseType.

#### Add Validation

You can further add additional validation besides the type validation of your config.
If you don't want to have any other validation besides the type, you can leave is as an empty list.
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

cfg.config_type["ADDON_CONFIG"] = (str, [_check_function]) # (5)!
```

1. Please use the `ConfigError` class from CocktailBerry.
2. Check function for config validation. First argument is the configname, second is the configvalue.
3. We just raise the exception if the value is "forbidden".
4. Failed validation should throw the `ConfigError`, other errors will crash the app.
5. You can define any number of check function. Please take care that the function interface has two arguments.


#### Validate List Settings

An extra case is, if your setting is a list of values.
In this case, you need to tell the config object which type the list elements are.
This info is stored in the `config_type_list` dictionary.
Use the same name, as your config name. 
The schema is identical as before, you must define the type, as well can define validation functions, as before.
Take note that currently no nested lists are supported and each list element need to have the same type.

```python
if not hasattr(cfg, 'ADDON_LIST'):  # (1)!
    cfg.ADDON_LIST = [1,2,3]  # type: ignore
cfg.config_type["ADDON_LIST"] = (list, []) # (2)!
cfg.config_type_list["ADDON_LIST"] = (int, []) # (3)!
```

1. Lists are set up the same like other values.
2. Most lists have no validation, but you may want to set a minimum or maximum number of elements for the check function.
3. Now you also need to provide the type and optional the validation for the list elements.


#### Add GUI Description

Optionally, you can add an additional description to your configuration.
This helps users using the GUI understanding the value better.
Use the `UI_LANGUAGE` object and it's according dialog dictionary.
The translation for the setting is in the `settings_dialog` key.
You then add your own config name as key into the setting and define the translations.
At least english is needed, if you do not provided a full list of translations.
If you don't want to provide GUI description, you can skip this step.
But it is encouraged to do so to improve user experience.

```python
from src.dialog_handler import UI_LANGUAGE as uil # (1)!

uil.dialogs["settings_dialog"]["ADDON_CONFIG"] = {
    "en": "English description",
    "de": "Deutsche Beschreibung",
} # (2)!
```

1. You need to import the `UI_LANGUAGE` object to access the dialogues
2. Optional, if you don't provide any value, no description is shown. You need to access the `settings_dialog` and then add your config name as a key. If you do so, the dictionary needs at least the english (`en`) key!

#### Using Selection for Dropdown

You may want to only offer a selection of values to the user.
In this case, you must define a class inheriting from the `ChooseType`.
The class needs to have the allowed values as allowed attribute.
The GUI will then display a drop down, only showing the allowed values.


```python
from src.config_manager import ChooseType # (1)!

SUPPORTED_TO_CHOOSE = ["List", "of", "allowed", "values"]
class AddOnChoose(ChooseType): # (2)!
    allowed = SUPPORTED_TO_CHOOSE

### Using selection type ###
if not hasattr(cfg, 'ADDON_CHOOSE_CONFIG'):
    cfg.ADDON_CHOOSE_CONFIG = "allowed"  # type: ignore
# Using the provided _build_support_checker for selection type
# provide your valid values
cfg.config_type["ADDON_CHOOSE_CONFIG"] = (AddOnChoose, []) # (3)!
```

1. Import the `ChooseType` from CocktailBerry to define selection.
2. Inherit from the class and define your allowed list of elements. The elements will be of type string due to the QtComboBox element, so in case you need other types, you have to convert the value later in your code.
3. The rest is similar to the other elements. Just make sure you set your defined class instead of the type.

### Using the Logger

The best way to implement logging into your addon is to use the internal CocktailBerry logger.
This way, your logs are saved and formatted the same way as the other logs.
This makes it easy for the user to view them over the GUI.
The logger takes two arguments: The log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL") and the log message.

```python
from src.logger_handler import LoggerHandler # (1)!
_logger = LoggerHandler("ADDON: Name") # (2)!

def init():
  _logger.log_event(
    "INFO",
    "ADDON NAME has been initialized successfully"
  ) # (3)!
```

1. Import the `LoggerHandler` from CocktailBerry to set up your logger.
2. Give the logger a name, it will be shown in the logs to pinpoint the messages. As a suggestion: use *ADDON: YourName* as the logger name, so it's clear the message comes from an addon.
3. The logger uses the base python logger in the background but delivers an abstraction. Levels are "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

### Prevent Cocktail Preparation

Your addon may want to check some condition before cocktail preparation.
This way, you can prevent the preparation of the cocktail.
For example, you your scale does not recognize a glass, a cocktail should not be prepared.
To break the preparation process, raise a RuntimeError. 
Please do not use other Error types, because only this type will be caught and handled.
You can provide an error message in either english, or an according translation for the current language.
You do not provide all languages if you do an translation, but you need at least the english one.
The error message will be shown as a dialog to the user, so it should explain why the cocktail was not prepared.

```python
def start():
    everything_ok = your_custom_check_logic() # (1)!
    # You can either just use direkt message in english
    # Or provide translations and use cfg.UI_LANGUAGE
    msg = {
        "en": "Englisch Error Message",
        "de": "Deutsche Fehlernachricht"
    } # (2)!
    # If not everything is ok, raise a RuntimeError
    if not everything_ok:
        message = msg.get(cfg.UI_LANGUAGE, msg["en"]) # (3)!
        raise RuntimeError(msg[message]) # (4)!
```

1. Insert your custom logic to check on condition or external devices if everything is as it should be.
2. You can either directly provide the message, or again define a translation. In the latter, see handling below. If you do provide translation, please make sure english is at least present.
3. When you do the language selection here, it is best to fall back to `en` on a not found key. This is useful when a new language is released, which your addon currently does not support. Otherwise a KeyError will crash the program.
4. Please raise a `RuntimeError`, other errors will not be caught and crash the program. The used message will be shown to the user.

### Provide Documentation

In case your addon will use other external dependencies (Python libraries), please provide some sort of installation guide.
The easiest way would be information in the readme of your project, that instructs the user which commands are necessary to get the addon running.
Also, if your configuration values are more complex or do need additional context, it is best practice to also provide documentation for them.
This will reduce user confusion an will raise the popularity of your addon.

If you created a cool addon, you can link me the project.
It may be included here, after it's functionality has been verified.
This way, more users may find the addon and can use it.