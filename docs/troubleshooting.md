# Troubleshooting

If you run into any problems, check here first for a solution.
Please ensure that you are running the latest 64 bit Raspberry Pi OS and CocktailBerry version.
If you don't find any solution here, you can [open a ticket](https://github.com/AndreWohnsland/CocktailBerry/issues/new/choose).

## Problems while Running the Program

All cases (e.g. not enough of one ingredient, no/wrong values ...) should be handled, and an info message should be displayed.
If in any case any unexpected behavior occurs, feel free to open an issue.
Usually, a part of the actions are also logged into the log files.
When submitting an error, please also provide the `logs/debuglog.log` file.

## Icons are Missing

If some of the icons (check / cross on the checkbox, up / down arrow on the list view) are missing, make sure you run the script within the folder (e.g. `python runme.py`) and not from another folder (e.g. `CocktailBerry/runme.py`).
This is because of the nature of Qt and the translation to python, if you go from another folder the picture ressources can't be found.

Another reason may be, if you are using a custom style sheet with colors using rgb.
If thats the case, please change the color codes to the hexadecimal representation of the color, because qtawesome can't handle rgb color codes.

## Changing Volume Unit

For the users of the machine, there is the possibility to set the `EXP_MAKER_UNIT` and `EXP_MAKER_FACTOR` option to change the displayed unit, for example to oz.
Please take note that the units stored in the database are still in ml, and if inserting new recipes, you still need to provide them in ml.
This feature is purely cosmetic and for the user of the maker tab when making cocktails, that no calculations need to be done while making cocktails.

## Restoring Database

Some of the migrations create a backup of the database before doing the mutation steps, like adding new recipes.
If you rather don't want to have the new recipes, you can overwrite the local `Cocktail_database.db` with the `Cocktail_database_backup.db` file.

```bash
cp Cocktail_database_backup-{your-date-string}.db Cocktail_database.db
```

This will restore the state of the backup previous this migration step.
Please take a look into the production_log file, if a backup was created.
Otherwise, you may up ending using an older one.
A backup is usually only done in migration steps which are optional, like adding new recipes.

## Using a High Resolution Screen

The UI of the program is somewhat dynamic, but Qt got it's limitations.
To ensure that the UI looks nice like in the screenshots, a resolution not higher than ~1200px on the long side (width) is recommended.
If you happen to use a high res screen, there is a easy fix, tough.
For example, when using a screen with a 2560x1600 resolution, I would recommend divide the value by `x` (for example x=2).
In the CocktailBerry config set width to 2560/2 = 1280 and height to 1600/2 = 800.
In case you used the provided setup, just change the first line in the ~/launcher.sh file `export QT_SCALE_FACTOR=1` from 1 to x (2 in the example case).
This will use the lower dimensions for the application but scale it up by the factor of two so it occupies the whole screen.
Decimal numbers for x do also work, just try not to get decimals for width / height.
If you use your own startup script or similar, just add the export line with an according value to it, or set the environment variable in any other desired way.


## Touchscreen Calibration

Sometimes you need to calibrate your touchscreen, otherwise the touched points and cursor are out of sync.
First you need to get and compile xinput.
After that, you can execute the program and select the crosses on the touchscreen according to the shown order.

```bash
wget http://github.com/downloads/tias/xinput_calibrator/xinput_calibrator-0.7.5.tar.gz
tar -zxvf xinput_calibrator-0.7.5.tar.gz
cd xinput_calibrator-0.7.5
sudo apt-get install libx11-dev libxext-dev libxi-dev x11proto-input-dev
./configure
make
sudo make install
sudo xinput_calibrator # sudo DISPLAY=:0.0 xinput_calibrator may also work
```

To adjust those new touch coordinates, they need to be saved. The xinput program should print out some block beginning with `Section "InputClass"` and ending with `EndSection`. This part needs to be copied to the `99-calibration.conf` file.

```bash
sudo mkdir /etc/X11/xorg.conf.d
sudo nano /etc/X11/xorg.conf.d/99-calibration.conf
```

After the reboot, the calibration should be okay.

## How to Have the Right Time

There is the config value `MAKER_CHECK_INTERNET`.
If you wish to use your microservice, but got no internet at the moment, the data will be saved and send later.
One problem that occurred, is that, for example on a standard Raspberry Pi, the clock and therefore the timestamp will probably be wrong.
This new option tackles that. If it's set active with an active microservice, it will check for internet connection at startup.
If there is no connection, a dialog will pop up and give the user the possibility to adjust the time.
In case the machine got a RTC build in and uses it, this option can usually be set to `false`, because due to the RTC, the time should be correct.

## Get the LED Working

Getting the WS281x to work may be a little bit tricky.
You MUST run the program as sudo (`sudo python runme.py`), so you also need to change this in `~/launcher.sh`.
If the GUI looks different than when you run it without sudo, try `sudo -E python runme.py` this should use your environment for Qt.
If you ran the program as non root, you will need to install the required python packages for the main program with sudo pip install.
Also, install the rpi_ws281x python package with:

```bash
sudo pip install rpi_ws281x
sudo pip install requests pyyaml GitPython typer pyfiglet qtawesome piicodev mfrc522 qtsass pyqtspinner
```

See [here](https://github.com/jgarff/rpi_ws281x#gpio-usage) for a possible list and explanation for GPIOs.
I had success using the 12 and 18 PWM0 pin, while also disabling (use a # for comment) the line `#dtparam=audio=on` on `/boot/config.txt`.
Other described pins may also work, but are untested, so I recommend to stick to the both one that should work.
If you use any other non controllable LED connected over the relay, you can use any pin you want, since it's only activating the relay.

## Set Up RFID Reader

Setting up a RFID reader and integrate it into the program is an intermediate task.
So I would not recommend it for complete beginners, and it may include some tinkering.
Currently you can use two different types of reader:

- Basic MFRC522 ([like this](https://www.amazon.de/dp/B074S8MRQ7), SPI Protocol)
- PiicoDev RFID ([only this](https://core-electronics.com.au/piicodev-rfid-module.html), I2C Protocol)

!!! bug "Please Read"
    Reading / Writing RFIDs while still having a interactive GUI may cause a lot of troubles.
    Some reader frameworks lock themselves until the read or write is done and have no direct cancel methods.
    So even using threads only fixes the responsiveness of the app.
    Therefore, the best is if you trigger a write, finish the write. 
    If you have experience with the reader + python feel free to contact me, so we can improve this feature.

Setting them up is described [here for the MFRC522](https://pimylifeup.com/raspberry-pi-rfid-rc522/) and [here for the PiicoDev](https://core-electronics.com.au/guides/piicodev-rfid-module-guide-for-raspberry-pi/).
You only need the wiring and the installation of the libraries.
The according code is integrated into CocktailBerry.
After that, you select the according option in the settings dropdown for the reader.
When using the teams function, you can then also use a rfid chip, which inserts the information (name of person) for the leaderboard.
In addition, when going to the settings tab, the option to write a string (name) to a chip is enabled.

Take care that you don't use any of the connected pins of the RFID reader in the CocktailBerry config for a pump or a LED.
If you do so, remove them or replace them with another pin.
Otherwise, the RFID will not work.
Best is to restart the Pi afterwards and then check if the RFID is working as intended.

## Ui Seems Wrong on none RaspOS System

On different Linux systems (other than the recommended Raspbian OS), there may be differences in the look and functionality of the user interface.
This can be dependant on the flavour of Linux, as well as the desktop variant you are using.
I had best experience when using a LXDE/XFCE variant, for example of a Debian Linux, on a none Raspberry Pi single board computer.
Other desktop variants may do not respect the always on top property, resulting in the taskbar show up on top the app when running the program and pop ups appear.
Please take note that CocktailBerry will run on other systems than the Raspberry Pi OS and RPi, but may take some tweaking and testing in the settings.
Since I probably don't own that combination of Hardware and OS, you probably need to figure out that settings by yourself.
If you are a unexperienced user with Linux, I recommend you stick to the recommended settings on a Pi.

## Task Bar Overlap / Push GUI

This may happen (especially at older versions os RPi OS or higher res screens) when running the program and some dialog window opens.
The task bar (bar with programs on it) may overlap the dialog window or push it down by it's height.
Ensure that you have unchecked the "Reserve space, and not covered by maximised windows" option.
You can find it under the panel preferences (right click the task bar > panel settings > Advanced).
Unchecking this box usually fixes this problem.

## Reset Config

In case you want to reset the configuration, it is the best way to just delete the custom_config.yaml in the main folder.
This file holds your configuration and will be created with the defaults if it does not exists.

If some setting is not working and prevents a program start, you can also edit the config file manually.
The config file is located at `~/CocktailBerry/custom_config.yaml`.
You can open it with any text editor.
Or just use the terminal:

```bash
cd ~/CocktailBerry
sudo nano custom_config.yaml
# use the arrow keys to navigate
# ctrl + o to save
# ctrl + x to exit
```

## Software does not Update

It may happen that you don't get the latest version of the software prompted at start, even if you check for updates.
This can be due to different reasons.
First, check if you have a internet connection.
If you have, check if you have the latest recommended version of python installed.
CocktailBerry will not show the update if the future needed python version is higher than the current installed one.
Another reason may be that your git file is corrupted.
Check with for errors like object file x is empty:

```sh
cd ~/CocktailBerry
git status
git pull
# if error occurs you can try to fix it with
find .git/objects/ -type f -empty | xargs rm
git fetch -p
git fsck --full
``` 

This should not only remove the corrupted files, but also fetch the latest version of the software.
If you get another error output, it is best to submit the error output with the issue.

## Problems with Cocktail Pictures

With the v1.30.0 release, the maker view was completely rewritten.
This includes the way cocktails are shown as a list and single view.
There is a picture now for every cocktail, the default provided cocktails all got an according picture.
There is also a default picture for cocktails without a picture, like newly user added ones.
You can upload your own pictures over the according button the recipe tab.
Your picture will then replace the default provided picture.

The user pictures are stored in the `CocktailBerry/display_images_user` folder.
The picture will be saved with the cocktail id as name and jpg format. 
You can also provide the cocktail name in lowercase and underscore instead spaces as picture name in jpg format (e.g. `cuba_libre.jpg` for "Cuba Libre"), if you prefer to upload the pictures via hand in that folder instead of the GUI.

If your database is quite old, newer cocktails you added may either have the default picture, or may have another picture from new cocktails contained now in the database.
This is due to the database using incrementing integers as primary key for the cocktails.
This is historically and can't be changed easily in running installations.
If thats the case, please use the GUI option to replace wrong pictures with your desired ones.
If you feel that the default pictures are switched, you can also use the default ones as replacement.
They are located at `CocktailBerry/default_cocktail_images`.

Here is an extensive list of all default cocktails and their according image.
If you think your cocktail have the wrong picture, you can use the according picture name from the list below to replace it.

??? info "List of Default Pictures"

    | Cocktail Name         | Picture Name |
    | --------------------- | ------------ |
    | Cuba Libre            | 1.jpg        |
    | Rum Cola              | 2.jpg        |
    | Long Island           | 3.jpg        |
    | Swimming Pool         | 5.jpg        |
    | Pina Colada           | 6.jpg        |
    | Tequila Sunrise       | 7.jpg        |
    | Touch Down            | 8.jpg        |
    | Mai Tai               | 9.jpg        |
    | Strawberry Colada     | 10.jpg       |
    | Blue Lagoon           | 11.jpg       |
    | Zombie                | 13.jpg       |
    | Planters Punch        | 14.jpg       |
    | Acapulco Gold         | 15.jpg       |
    | Bahama Mama           | 17.jpg       |
    | Bahia ll              | 18.jpg       |
    | Käptn Chaos           | 19.jpg       |
    | Vodka Mara            | 20.jpg       |
    | Screwdriver (Vodka o) | 21.jpg       |
    | Mix Alabama           | 23.jpg       |
    | Blue Mara             | 24.jpg       |
    | Rum Sunrise           | 25.jpg       |
    | Hemingway             | 31.jpg       |
    | Amazon Cocktail       | 32.jpg       |
    | Black Sun             | 33.jpg       |
    | Bombay Punch          | 34.jpg       |
    | Sweet Kiss            | 39.jpg       |
    | Sex on the Beach      | 52.jpg       |
    | Malibu Beach          | 53.jpg       |
    | Indigo Birdman        | 54.jpg       |
    | Hurricane             | 55.jpg       |
    | Adios Motherfucker    | 56.jpg       |
    | Coco Loco             | 57.jpg       |
    | Gin Tonic             | 58.jpg       |
    | Beachbum              | 81.jpg       |
    | Bay Breeze            | 82.jpg       |
    | Belladonna            | 83.jpg       |
    | Black-Eyed Susan      | 84.jpg       |
    | Blue Hawaii           | 85.jpg       |
    | Blue Ricardo          | 86.jpg       |
    | Flamingo              | 87.jpg       |
    | Orange Crush          | 88.jpg       |
    | Bocce Ball            | 89.jpg       |
    | Fuzzy Navel           | 90.jpg       |
    | Madras                | 91.jpg       |
    | Woo Woo               | 92.jpg       |
    | Vodka Tonic           | 93.jpg       |
    | Sidewinder’s Fang     | 94.jpg       |
    | 212                   | 95.jpg       |
    | Cantarito             | 96.jpg       |
    | Paloma                | 97.jpg       |

Another way is to reinstall CocktailBerry and use the backup function, to have the latest version of the database.
When using the backup function, you should skip the database restoration, so you can use the new one.
Keep in mind your changes to the database are lost this way, so this may not be the best option for you.

## Problems Installing Software on Raspberry Pi

The Raspberry Pi can sometimes differ from other machines in terms of installation. Here are some issues that might occur.

### PyQt can't be Installed

You probably need to run `sudo apt install python3-pyqt5` instead of `pip install pyqt5` on the Pi. 

### Numpy Import Error at Matplotlib Import

Try first running `pip3 install -U numpy` and `sudo apt install libatlas3-base`.
If it is still not fixed, try uninstalling and installing numpy / matplotlib again.
If really nothing else works, try `sudo pip3 install -U numpy`, then you will probably need to run the python file with root privilege as well, which may result in another GUI style used by the system.

### How to get the GUI Running on Startup

I found the easiest thing is to use RPis Autostart.
Create a .desktop file with `sudo nano /etc/xdg/autostart/cocktail.desktop` and the `launcher.sh` in your `/home/pi` folder:

```
[Desktop Entry]
Type=Application
Name=CocktailScreen
NoDisplay=false
Exec=/usr/bin/lxterminal -e /home/pi/launcher.sh
```

```bash
#!/bin/bash
# launcher.sh for dashboard
# no need for sudo if there were no Numpy import errors
cd /home/pi/CocktailBerry/dashboard/qt-app/
sudo python main.py
```

```bash
#!/bin/bash
# launcher.sh for CocktailBerry
cd /home/pi/CocktailBerry/
python runme.py
```

If your setup is equal to mine (Raspberry Pi, CocktailBerry GitHub cloned to the home (`/home/pi/`) folder) you can also just copy the files and comment/uncomment within the launcher.sh to save some typing:

```bash
cp ~/CocktailBerry/scripts/launcher.sh ~/
cp ~/CocktailBerry/scripts/cocktail.desktop /etc/xdg/autostart/
```

If there are any problems with the lxterminal window opening and instant closing, check the rights of the shell file, it needs executable (x) rights, otherwise use `chmod` to give x-rights:

```bash
sudo chmod +x ~/launcher.sh
# or
sudo chmod 755 ~/launcher.sh
```

!!! info "By the Way"
    The provided installer script does all that steps for you.

### The GUI on the RPi Looks Different from the Screenshots

I've noticed when running as root (sudo python) and running as the pi user (python) by default the pi will use different GUI resources.
Using the pi user will result in the shown interfaces at CocktailBerry (and the program should work without root privilege).
Setting the XDG_RUNTIME_DIR to use the qt5ct plugin may also work but is untested.
Using the users environment with `sudo -E python runme.py` should also do the trick.

### Some Python Things do not Work

Older Raspberry Pi OS version (older than _November 2021_) still deliver Python 2.
Since Raspberry Pi OS Bullseye version (based on Debian 11) Python 3 is the default version if you type `python` or `pip`.
Typing `python --version` or `pip --version` will show your version of Python.
If it's still Python 2, consider upgrading your OS or check `python3 --version` and use the `pip3` as well as the `python3` command instead the usual ones.
