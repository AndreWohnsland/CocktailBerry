# Setting up CocktailBerry

CocktailBerry will work directly after using the installer, but you can make your own adjustments to make it even better.

## Adding new Recipes or Ingredients

CocktailBerry comes with a limited set of recipes and ingredients.
You can use the program to add your own ingredients or recipes, or rename and change existing ones.
Just use the implemented UI for the procedure under the according tabs (**Ingredients** or **Recipes**).
All entered values are checked for reason and if something is wrong, an error message will inform the user what is wrong with the data input.

!!! info "Database Structure"
    If you want to browse through the data in the database, I recommend some program like [DB Browser for SQLite](https://sqlitebrowser.org/).
    You can view the DB schema [here](https://github.com/AndreWohnsland/CocktailBerry/blob/master/docs/.devnotes.md#db-schema).

## Setting up the Machine / Modifying other Values

You can manage your config within CocktailBerry.
Just go to the bottles tab (v1), click the gear icon or to the according option tab (v2) and enter your password.
You can then use the UI to change the configuration.
The configuration is also divided into own tabs, containing similar categories in one tab.

These values are stored under the local `custom_config.yaml` file.
This file will be created at the first machine run and inherit all default values.
Depending on your pumps and connection to the Pi, these can differ from the default and can be changed.
If any of the values got a wrong data type, a message with the issue will be shown.
Names starting with `EXP` are experimental and may be changed in the future.
They can be used at own risk of CocktailBerry not working 100% properly.

??? info "List UI Config Values"
    UI Config Values are used to change the look and feel of the program.

    | Value Name          | Description                                                           |
    | :------------------ | :-------------------------------------------------------------------- |
    | `UI_DEVENVIRONMENT` | Enables some development features, like a cursor                      |
    | `UI_MASTERPASSWORD` | Number Password for System/Program Level                              |
    | `UI_MAKER_PASSWORD` | Number Password for party operation                                   |
    | `UI_LOCKED_TABS`    | Specify, which tab to lock with maker password                        |
    | `UI_LANGUAGE`       | 2 char code for the language, see [supported languages](languages.md) |
    | `UI_WIDTH`          | Desired interface width, default is 800                               |
    | `UI_HEIGHT`         | Desired interface height, default is 480                              |
    | `UI_PICTURE_SIZE`   | Approximate displayed picture size                                    |
    | `UI_ONLY_MAKER_TAB` | Only allow access to the maker tab                                    |
    | `MAKER_THEME`       | Choose which [theme](#themes) to use                                  |

??? info "List Maker Config Values"
    Maker config values are used to change the behavior of CocktailBerry.

    | Value Name                    | Description                                               |
    | :---------------------------- | :-------------------------------------------------------- |
    | `MAKER_NAME`                  | Give your CocktailBerry an own name, max 30 chars         |
    | `MAKER_NUMBER_BOTTLES`        | Number of displayed bottles, can use up to 16 bottles     |
    | `MAKER_PREPARE_VOLUME`        | List of possible spend volumes of machine                 |
    | `MAKER_SIMULTANEOUSLY_PUMPS`  | Number of pumps which can be simultaneously active        |
    | `MAKER_SEARCH_UPDATES`        | Search for updates at program start                       |
    | `MAKER_CHECK_BOTTLE`          | Check if there is enough of each ingredient left          |
    | `MAKER_CLEAN_TIME`            | Time the machine will execute the cleaning program        |
    | `MAKER_ALCOHOL_FACTOR`        | Value to multiply alcoholic ingredients in all recipes    |
    | `MAKER_MAX_HAND_INGREDIENTS`  | Max x ingredients are allowed to add by hand              |
    | `MAKER_CHECK_INTERNET`        | Do a connection check at start for time adjustment window |
    | `MAKER_USE_RECIPE_VOLUME`     | Do not scale but use defined amounts                      |
    | `MAKER_ADD_SINGLE_INGREDIENT` | Allows spending single ingredient in maker view           |

??? info "List Hardware Config Values"
    Hardware config values are used to configure and enable the connected hardware.

    | Value Name                    | Description                                                                                     |
    | :---------------------------- | :---------------------------------------------------------------------------------------------- |
    | `MAKER_PINS_INVERTED`         | [Inverts](faq.md#what-is-the-inverted-option) pin signal (on=low, off=high)                     |
    | `PUMP_CONFIG`                 | List with config for each pump: pin, volume flow, tube volume to pump up                        |
    | `MCP23017_CONFIG`             | Config for MCP23017 I2C GPIO expander (16 pins, 0-15)                                           |
    | `PCF8574_CONFIG`              | Config for PCF8574 I2C GPIO expander (8 pins, 0-7)                                              |
    | `LED_NORMAL`                  | List of normal (non-addressable) LED configs: pin, default on, prep state                       |
    | `LED_WSLED`                   | List of WS281x (addressable) LED configs: pin, brightness, count, rings, default on, prep state |
    | `RFID_READER`                 | Enables connected RFID reader, [more info](troubleshooting.md#set-up-rfid-reader)               |
    | `MAKER_PUMP_REVERSION_CONFIG` | Enables reversion (direction) of pump during cleaning                                           |

??? info "List Software Config Values"
    Software config values are used to configure additional connected software and its behavior.

    | Value Name              | Description                                                |
    | :---------------------- | :--------------------------------------------------------- |
    | `MICROSERVICE_ACTIVE`   | Post to microservice set up by docker                      |
    | `MICROSERVICE_BASE_URL` | Base URL for microservice (default: http://127.0.0.1:5000) |
    | `TEAMS_ACTIVE`          | Use teams feature                                          |
    | `TEAM_BUTTON_NAMES`     | List of format ["Team1", "Team2"]                          |
    | `TEAM_API_URL`          | Endpoint of teams API, default used port by API is 8080    |

??? info "Payment Related Config Values"
    Payment config values are used to configure the payment system and its behavior.

    General Payment Config:

    | Value Name                  | Description                                                    |
    | :-------------------------- | :------------------------------------------------------------- |
    | `PAYMENT_TYPE`              | Type of payment integration to use                             |
    | `PAYMENT_PRICE_ROUNDING`    | Next multiple of this number to round up to                    |
    | `PAYMENT_VIRGIN_MULTIPLIER` | Multiplier percentage to apply to virgin cocktail prices       |
    | `PAYMENT_TIMEOUT_S`         | Timeout in seconds before reader cancels payment NFC/RFID scan |


    CocktailBerry Payment Service Config:

    | Value Name                         | Description                                                 |
    | :--------------------------------- | :---------------------------------------------------------- |
    | `PAYMENT_SHOW_NOT_POSSIBLE`        | Show cocktails that are not possible to the user            |
    | `PAYMENT_LOCK_SCREEN_NO_USER`      | Lock the screen when no user is logged in                   |
    | `PAYMENT_SERVICE_URL`              | URL of the payment service API                              |
    | `PAYMENT_SECRET_KEY`               | Secret key for authentication with the payment service      |
    | `PAYMENT_AUTO_LOGOUT_TIME_S`       | Time in seconds until automatic logout of user from payment |
    | `PAYMENT_LOGOUT_AFTER_PREPARATION` | Remove user for filtering cocktail view after preparation   |

    SumUp Specific Config:

    | Value Name                    | Description                                               |
    | :---------------------------- | :-------------------------------------------------------- |
    | `PAYMENT_SUMUP_API_KEY`       | Secret key for authentication with the payment service    |
    | `PAYMENT_SUMUP_MERCHANT_CODE` | Merchant code for authentication with the payment service |
    | `PAYMENT_SUMUP_TERMINAL_ID`   | Terminal ID for authentication with the payment service   |

??? info "List Other Config Values"
    Here are some other config values, which are not fitting in the other categories.
    Addon data will be added here as well.

    | Value Name         | Description                                                  |
    | :----------------- | :----------------------------------------------------------- |
    | `EXP_MAKER_UNIT`   | Change the displayed unit in the maker tab (visual only\*)   |
    | `EXP_MAKER_FACTOR` | Multiply the displayed unit in the maker tab (visual only\*) |

    \* You still need to provide the units in ml for the DB (recipes / ingredients).
    This is purely visual in the maker tab, at least for now.
    If you want to display oz in the maker tab, use 'oz' and 0.033814 for unit and factor.

Depending on your preferred use, these values can differ.
Customizing and using your own setting will make your CocktailBerry unique.

## Setting your Ingredients

The choice is up to you what you want to connect.
See [here](#possible-ingredient-choice) for a possible ingredient setting.
Select under **Bottles** your assigned ingredients for each pump.
In addition, you can define ingredients which are available, but are not connected to the machine (under **Bottles** >  _available_).
This can be ingredients, which would not be optimal for your pump (sticky), or are only very rarely used in cocktails.
At the ingredient properties, you can set this ingredient only addable by hand.
These ingredients are not shown in the bottle dropdown but only at the available window.
Choose this option for ingredients you won't connect to the machine, to reduce the amount of options displayed at the dropdown.

The program will then evaluate which recipe meets all requirements to only show the recipes where all existing ingredients (machine + hand) exist.
All possible recipes will be shown in the **Maker** Tab.
See also [this FAQ](faq.md#what-is-the-available-button) for more information on this topic.

## Configuring the Pins or used Board

Most boards should work with CocktailBerry, the according controller will be automatically selected.
Currently supported options (boards) are:

- **RPI (Raspberry Pi)**: Using GPIO according to [GPIO-Numbers](https://pinout.xyz/) for Pins.
- **Generic**: Using GPIO with [python-periphery](https://github.com/vsergeev/python-periphery). Should work for many boards, check out your GPIO number from your provider.

!!! info "Not your Board?"
    Even if your board is not listed here, it may work.
    This value is used to determinate the control method for the pins of the board.

## Themes

Currently, there are following themes:

- **default**: The look and feel of the project pictures. Blue, Orange and Black as main colors.
- **bavaria**: The somewhat light mode of the app. Blue, Black and White as main colors.
- **berry**: Pink mixed with dark blue and dark background.
- **alien**: Different shades of green and dark background.
- **tropical**: Bright colors with yellow and light blue.
- **purple**: It's purple and light blue.
- **custom**: Starts by the default theme, but you can set each color to your liking.

## Calibration of the Pumps

You can either use the CocktailBerry program to get to the calibration - it's located under your settings (option gear).
This will start the calibration overlay.
You can use water and a weight scale for the process.
Use different volumes (for example 10, 20, 50, 100 ml) and compare the weight with the output from the pumps.
In the end, you can adjust each pump volume flow by the factor:

$$ \dot{V}_{new} = \dot{V}_{old} \cdot \dfrac{V_{output}}{V_{expectation}} $$

Do a mix of the different volumes, add them together and check if the scale shows the same amount at each pump.

## Cleaning the Machine

CocktailBerry has a build in cleaning function for cleaning at the end of a party.
You will find the feature at the option gear under the **Bottles** tab.
CocktailBerry will then go to cleaning mode for the defined time within the config (default is 20 seconds).
A message prompt will inform the user to provide enough water for the cleaning process.

!!! question "When to Clean"
    Depending on the build specification of your machine, it is a good practice to execute the cleaning of the machine before and after usage.
    This depends on the frequency you use CocktailBerry, where it's stored, how good it was cleaned and so on.

If you have activated the the option of inverted current with `MAKER_PINS_INVERTED`, you will be prompted before the cleaning if you want to invert the current for the cleaning process.
This way, you can clean the tubes from both sides and get rid of all fluid in the end.

## Possible Ingredient Choice

If you are unsure, which ingredients you may need or want to connect to CocktailBerry, here is a quick suggestion.
You don't need to use all ten slots, but the more you use, the more recipes will be possible:

- Vodka
- White Rum
- Brown Rum
- Orange Juice
- Passion Fruit Juice
- Pineapple Juice
- _optional_ Gin
- _optional_ Malibu
- _optional_ Tequila
- _optional_ Grapefruit Juice

In addition, there are some ingredients recommend adding by hand, the most important additional ingredients will be:

- Soft drinks (Cola, Fanta, Sprite)
- Grenadine syrup
- Blue Curaçao
- Lemon juice (just a little, you can also use fresh lemons)
- _optional_ Cointreau (you may just not add it if not desired)

With this as your base set up, even if not using the optional ingredients, your CocktailBerry will be able to do plenty of different cocktails.

!!! tip "Data Insights"
    You can export the CocktailBerry data to a CSV file over the interface.
    Use the CocktailBerry UI in the options page to get a neat local overview of the data.
    With this information you may identify popular drinks and ingredients.

## Updates

There is the option to enable the automatic search for updates at program start.
The `MAKER_SEARCH_UPDATES` config can enable this feature.
CocktailBerry will then check the GitHub repository for new releases and informs the user about it.
If accepted, CocktailBerry will pull the latest version and restart the program afterwards.
The migrator will do any necessary steps to adjust local files, like the database to the latest release.

## Backups

You can backup your local data (local database, config-file) to a desired folder or external device.
Use this backup to restore the data, or recover the progress and recipes after doing a OS reinstall.
Just go to the **Bottles** tab, click on the gear icon and enter your master password to get to the options window.
There you will find both options for backup and restoring your data.
