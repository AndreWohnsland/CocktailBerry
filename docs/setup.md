# Setting up CocktailBerry

CocktailBerry will work after installing all requirements, but you can make your own adjustments.

## Adding new Recipes or Ingredients

There are only limited ingredients and recipes. But you can add your own data to the program as well.
This app uses a sqlite3 database coupled to the UI.
So, it's quite easy to implement new ingredients or even recipes.
Just use the implemented UI for the procedure under the according tabs (**Ingredients** or **Recipes**).

All entered values are checked for reason and if something is wrong, an error message will inform the user what is wrong with the data input.
If you want to browse through the database, I recommend some program like [DB Browser for SQLite](https://sqlitebrowser.org/).

## Setting up the Machine / Modifying other Values

You can also manage your config within CocktailBerry since __version 1.8.0__.
Just go to the bottles tab, click the gear icon and enter the password (default: 1234).
You can then use the UI to change the configuration.
These values are stored under the local `custom_config.yaml` file.
This file will be created at the first machine run and inherit all default values. 
Depending on your pumps and connection to the Pi, these can differ from mine and can be changed.
If any of the values got a wrong data type, a ConfigError will be thrown with the message which one is wrong.
Names starting with `EXP` are experimental and may be changed in the future.
They can be used at own risk of CocktailBerry not working 100% properly.

| Value Name              | Description                                                                          |
| :---------------------- | :----------------------------------------------------------------------------------- |
| `UI_DEVENVIRONMENT`     | Enables some development features, like a cursor                                     |
| `UI_PARTYMODE`          | Protects other tabs than maker tab with a password                                   |
| `UI_MASTERPASSWORD`     | String for password, Use numbers for numpad like '1234'                              |
| `UI_LANGUAGE`           | 2 char code for the language, see [supported languages](languages.md)                |
| `UI_WIDTH`              | Desired interface width, default is 800                                              |
| `UI_HEIGHT`             | Desired interface height, default is 480                                             |
| `PUMP_PINS`             | List of the [Pins](#configuring-the-pins-or-used-board) where each Pump is connected |
| `PUMP_VOLUMEFLOW`       | List of the according volume flow for each pump in ml/s                              |
| `MAKER_BOARD`           | Used [board](#configuring-the-pins-or-used-board) for Hardware                       |
| `MAKER_NAME`            | Give your CocktailBerry an own name, max 30 chars                                    |
| `MAKER_NUMBER_BOTTLES`  | Number of displayed bottles, can use up to 16 bottles                                |
| `MAKER_SEARCH_UPDATES`  | Search for updates at program start                                                  |
| `MAKER_THEME`           | Choose which [theme](#themes) to use                                                 |
| `MAKER_CLEAN_TIME`      | Time the machine will execute the cleaning program                                   |
| `MAKER_SLEEP_TIME`      | Interval between each time check while generating a cocktail                         |
| `MAKER_CHECK_INTERNET`  | Do a connection check at start for time adjustment window                            |
| `MAKER_TUBE_VOLUME`     | Volume in ml to pump up when bottle is set to new                                    |
| `MICROSERVICE_ACTIVE`   | Post to microservice set up by docker                                                |
| `MICROSERVICE_BASE_URL` | Base URL for microservice (default: http://127.0.0.1:5000)                           |
| `TEAMS_ACTIVE`          | Use teams feature                                                                    |
| `TEAM_BUTTON_NAMES`     | List of format ["Team1", "Team2"]                                                    |
| `TEAM_API_URL`          | Endpoint of teams API, default used port by API is 8080                              |
| `EXP_MAKER_UNIT`        | Change the displayed unit in the maker tab (visual only\*)                           |
| `EXP_MAKER_FACTOR`      | Multiply the displayed unit in the maker tab (visual only\*)                         |

\* You still need to provide the units in ml for the DB (recipes / ingredients).
This is purely visual in the maker tab, at least for now.
If you want to display oz in the maker tab, use 'oz' and 0.033814 for unit and factor.

Depending on your preferred use, these values can differ.

## Setting your Ingredients

The choice is up to you what you want to connect.
See [here](#possible-ingredient-choice) for a possible ingredient setting.
Select under **Bottles** your assigned ingredients for each pump over the dropdown boxes.
In addition, you can define ingredients which are also there, but are not connected to the machine (under **Bottles** >  _available_).
You can define ingredients in recipes (at _add self by hand_) which should be later added via hand, for example sticky ingredients.
This can be ingredients, which would not be optimal for your pump, or are only very rarely used in cocktails.

The program will then evaluate which recipe meets all requirements to only show the recipes where even the ingredients added via hand later are available.
All possible recipes will be shown in the **Maker** Tab.
See also [faq](faq.md#what-is-the-available-button) for more information on this topic.

## Configuring the Pins or used Board

To set up your Board, you can choose between different platforms.
The according controlling library for Python needs to be installed.
If it's not shipped within the default OS of your board, this will be mentioned here.
Currently supported options (boards) are:

- **RPI (Raspberry Pi)**: Using GPIO according to [GPIO-Numbers](https://en.pinout.xyz/) for Pins.

## Themes

Currently, there are following themes:

- **default**: The look and feel of the project pictures. Blue, Orange and Black as main colors.
- **bavaria**: The somewhat light mode of the app. Blue, Black and White as main colors.
- **berry**: Pink mixed with dark blue and dark background.
- **alien**: Different shades of green and dark background.

## Calibration of the Pumps

You can either use the CocktailBerry program to get to the calibration - it's located under your settings (option gear).
This will start the calibration overlay.
Or you can start the calibration program instead of CocktailBerry - you simply add the `--calibration` or `-c` flag to the python run command:

```bash
python runme.py --calibration 
# or just 
python runme.py -c
```

You can use water and a weight scale for the process.
Use different volumes (for example 10, 20, 50, 100 ml) and compare the weight with the output from the pumps.
In the end, you can adjust each pump volume flow by the factor:

Vnew = Vold \* expectation/output

$$ \dot{V}_{new} = \dot{V}_{old} \cdot \dfrac{V_{expectation}}{V_{output}} $$

## Cleaning the Machine

CocktailBerry has a build in cleaning function for cleaning at the end of a party.
You will find the feature at the option gear under the **Bottles** tab.
CocktailBerry will then go to cleaning mode for the defined time within the config (default is 20 seconds).
A message prompt will inform the user to provide enough water for the cleaning process.
I usually use a big bowl of warm water to cycle the pumps through one time before changing to fresh water.
Then running twice times again the cleaning program to fully clean all pumps from remaining fluid.

## Possible Ingredient Choice

If you are unsure, which ingredients you may need or want to connect to CocktailBerry, here is a quick suggestion.
You don't need to use all ten slots, but the more you use, the more recipes will be possible:

- Vodka
- White Rum
- Brown Rum
- Orange Juice
- Passion Fruit Juice
- Pineapple Juice
- *optional* Gin
- *optional* Malibu
- *optional* Tequila
- *optional* Grapefruit Juice

In addition, there are some ingredients I would recommend not adding via CocktailBerry but by hand, the most important additional ingredients will be:

- Soft drinks (Cola, Fanta, Sprite)
- Grenadine syrup
- Blue Curaçao
- Lemon juice (just a little, you can also use fresh lemons)
- *optional* Cointreau (you may just not add it if not desired)

With this as your base set up, even if not using the optional ingredients, your CocktailBerry will be able to do plenty of different cocktails.

## Updates

With __version 1.5.0__, there is the option to enable the automatic search for updates at program start.
The `MAKER_SEARCH_UPDATES` config can enable this feature.
CocktailBerry will then check the GitHub repository for new releases and informs the user about it.
If accepted, CocktailBerry will pull the latest version and restart the program afterwards.
The migrator will also do any necessary steps to adjust local files, like the database to the latest release.

## Backups

Since **version 1.9.0**, you can backup your local data (local database, config-file) to a desired folder or external device.
You can later use this backup to restore the data, or recover the progress and recipes after doing a OS reinstall.
Just go to the **Bottles** tab, click on the gear icon and enter your master password to get to the options window.
There you will find both options for backup and restoring your data.
