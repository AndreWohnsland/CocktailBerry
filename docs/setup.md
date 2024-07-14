# Setting up CocktailBerry

CocktailBerry will work after installing all requirements, but you can make your own adjustments.

## Adding new Recipes or Ingredients

There are only limited ingredients and recipes. But you can add your own data to the program as well.
This app uses a sqlite3 database coupled to the UI.
So, it's quite easy to implement new ingredients or even recipes.
Just use the implemented UI for the procedure under the according tabs (**Ingredients** or **Recipes**).
All entered values are checked for reason and if something is wrong, an error message will inform the user what is wrong with the data input.

!!! info "Database Structure"
    If you want to browse through the data in the database, I recommend some program like [DB Browser for SQLite](https://sqlitebrowser.org/).
    You can view the DB schema [here](https://github.com/AndreWohnsland/CocktailBerry/blob/master/docs/.devnotes.md#db-schema).

## Setting up the Machine / Modifying other Values

You can manage your config within CocktailBerry.
Just go to the bottles tab, click the gear icon and enter the password (default: 1234 on older versions or none at latest).
You can then use the UI to change the configuration.
The configuration is also divided into own tabs, containing similar categories in one tab.

These values are stored under the local `custom_config.yaml` file.
This file will be created at the first machine run and inherit all default values.
Depending on your pumps and connection to the Pi, these can differ from mine and can be changed.
If any of the values got a wrong data type, a ConfigError will be thrown with the message which one is wrong.
Names starting with `EXP` are experimental and may be changed in the future.
They can be used at own risk of CocktailBerry not working 100% properly.

??? info "List UI Config Values"
    UI Config Values are used to change the look and feel of the program.

    | Value Name          | Description                                                           |
    | :------------------ | :-------------------------------------------------------------------- |
    | `UI_DEVENVIRONMENT` | Enables some development features, like a cursor                      |
    | `UI_PARTYMODE`      | Protects other tabs than maker tab with a password, deprecated        |
    | `UI_MASTERPASSWORD` | Number Password for System/Program Level                              |
    | `UI_MAKER_PASSWORD` | Number Password for party operation                                   |
    | `UI_LOCKED_TABS`    | Specify, which tab to lock with maker password                        |
    | `UI_LANGUAGE`       | 2 char code for the language, see [supported languages](languages.md) |
    | `UI_WIDTH`          | Desired interface width, default is 800                               |
    | `UI_HEIGHT`         | Desired interface height, default is 480                              |
    | `UI_PICTURE_SIZE`   | Approximate displayed picture size                                    |
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
    | `MAKER_MAX_HAND_INGREDIENTS`  | Max x ingredients are allowed to add by hand              |
    | `MAKER_CHECK_INTERNET`        | Do a connection check at start for time adjustment window |
    | `MAKER_TUBE_VOLUME`           | Volume in ml to pump up when bottle is set to new         |
    | `MAKER_USE_RECIPE_VOLUME`     | Do not scale but use defined amounts                      |
    | `MAKER_ADD_SINGLE_INGREDIENT` | Allows spending single ingredient in maker view           |

??? info "List Hardware Config Values"
    Hardware config values are used to configure and enable the connected hardware.

    | Value Name             | Description                                                                              |
    | :--------------------- | :--------------------------------------------------------------------------------------- |
    | `PUMP_PINS`            | List of the [Pins](#configuring-the-pins-or-used-board) where each Pump is connected     |
    | `PUMP_VOLUMEFLOW`      | List of the according volume flow for each pump in ml/s                                  |
    | `LED_PINS`             | List of pins connected to LEDs for preparation                                           |
    | `LED_BRIGHTNESS`       | Brightness for the WS281x LED (1-255)                                                    |
    | `LED_COUNT`            | Number of LEDs on the WS281x                                                             |
    | `LED_NUMBER_RINGS`     | Number of IDENTICAL daisy chained WS281x LED rings                                       |
    | `LED_DEFAULT_ON`       | Always turn on to a white LED by default                                                 |
    | `LED_IS_WS`            | Is the led a controllable WS281x LED, [see also](troubleshooting.md#get-the-led-working) |
    | `RFID_READER`          | Enables connected RFID reader, [more info](troubleshooting.md#set-up-rfid-reader)        |
    | `MAKER_BOARD`          | Used [board](#configuring-the-pins-or-used-board) for Hardware                           |
    | `MAKER_PINS_INVERTED`  | [Inverts](faq.md#what-is-the-inverted-option) pin signal (on=low, off=high)              |
    | `MAKER_PUMP_REVERSION` | Enables reversion (direction) of pump                                                    |
    | `MAKER_REVERSION_PIN`  | [Pin](#configuring-the-pins-or-used-board) which triggers reversion                      |

??? info "List Software Config Values"
    Software config values are used to configure additional connected software and its behavior.

    | Value Name              | Description                                                |
    | :---------------------- | :--------------------------------------------------------- |
    | `MICROSERVICE_ACTIVE`   | Post to microservice set up by docker                      |
    | `MICROSERVICE_BASE_URL` | Base URL for microservice (default: http://127.0.0.1:5000) |
    | `TEAMS_ACTIVE`          | Use teams feature                                          |
    | `TEAM_BUTTON_NAMES`     | List of format ["Team1", "Team2"]                          |
    | `TEAM_API_URL`          | Endpoint of teams API, default used port by API is 8080    |

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
Select under **Bottles** your assigned ingredients for each pump over the dropdown boxes.
In addition, you can define ingredients which are also there, but are not connected to the machine (under **Bottles** >  _available_).
You can define ingredients (with _only add self by hand_) which should be later added via hand.
This can be ingredients, which would not be optimal for your pump (sticky), or are only very rarely used in cocktails.
These ingredients are not shown in the bottle dropdown but only at the available window.
Choose this option for ingredients you won't connect to the machine, to reduce the amount of options displayed at the dropdown.

The program will then evaluate which recipe meets all requirements to only show the recipes where all existing ingredients (machine + hand) exist.
All possible recipes will be shown in the **Maker** Tab.
See also [this FAQ](faq.md#what-is-the-available-button) for more information on this topic.

## Configuring the Pins or used Board

To set up your Board, you can choose between different platforms.
The according controlling library for Python needs to be installed.
If it's not shipped within the default OS of your board, this will be mentioned here.
Currently supported options (boards) are:

- **RPI (Raspberry Pi)**: Using GPIO according to [GPIO-Numbers](https://pinout.xyz/) for Pins.
- **Generic**: Using GPIO with [python-periphery](https://github.com/vsergeev/python-periphery). Should work for many boards, check out your GPIO number from your provider.

!!! info "Not your Board?"
    Even if your board is not listed here, it may work.
    This value is used to determinate the control method for the pins of the board.
    If it's controlled identical to a listed board here, you can try to use this existing value for your board.

## Themes

Currently, there are following themes:

- **default**: The look and feel of the project pictures. Blue, Orange and Black as main colors.
- **bavaria**: The somewhat light mode of the app. Blue, Black and White as main colors.
- **berry**: Pink mixed with dark blue and dark background.
- **alien**: Different shades of green and dark background.
- **custom**: Starts by the default theme, but you can set each color to your liking.

## Calibration of the Pumps

You can either use the CocktailBerry program to get to the calibration - it's located under your settings (option gear).
This will start the calibration overlay.
Or you can start the calibration program instead of CocktailBerry.
You simply add the `--calibration` or `-c` flag to the python run command:

```bash
python runme.py --calibration 
# or just 
python runme.py -c
```

You can use water and a weight scale for the process.
Use different volumes (for example 10, 20, 50, 100 ml) and compare the weight with the output from the pumps.
In the end, you can adjust each pump volume flow by the factor:

$$ \dot{V}_{new} = \dot{V}_{old} \cdot \dfrac{V_{output}}{V_{expectation}} $$

I usually do a mix of the different volumes, add them together and check if the scale shows the same amount at each pump.

## Cleaning the Machine

CocktailBerry has a build in cleaning function for cleaning at the end of a party.
You will find the feature at the option gear under the **Bottles** tab.
CocktailBerry will then go to cleaning mode for the defined time within the config (default is 20 seconds).
A message prompt will inform the user to provide enough water for the cleaning process.
I usually use a big bowl of warm water to cycle the pumps through one time before changing to fresh water.
Then running twice times again the cleaning program to fully clean all pumps from remaining fluid.

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

In addition, there are some ingredients I would recommend not adding via CocktailBerry but by hand, the most important additional ingredients will be:

- Soft drinks (Cola, Fanta, Sprite)
- Grenadine syrup
- Blue Curaçao
- Lemon juice (just a little, you can also use fresh lemons)
- _optional_ Cointreau (you may just not add it if not desired)

With this as your base set up, even if not using the optional ingredients, your CocktailBerry will be able to do plenty of different cocktails.

!!! tip "Data Insights"
    You can export the CocktailBerry data to a CSV file over the interface.
    With this information you may identify popular drinks and ingredients.
    You can also use the CocktailBerry UI in the options page to get a neat local overview of the data.

## Updates

There is the option to enable the automatic search for updates at program start.
The `MAKER_SEARCH_UPDATES` config can enable this feature.
CocktailBerry will then check the GitHub repository for new releases and informs the user about it.
If accepted, CocktailBerry will pull the latest version and restart the program afterwards.
The migrator will also do any necessary steps to adjust local files, like the database to the latest release.

## Backups

You can backup your local data (local database, config-file) to a desired folder or external device.
You can later use this backup to restore the data, or recover the progress and recipes after doing a OS reinstall.
Just go to the **Bottles** tab, click on the gear icon and enter your master password to get to the options window.
There you will find both options for backup and restoring your data.
