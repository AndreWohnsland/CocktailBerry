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
cp Cocktail_database_backup.db Cocktail_database.db
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

With version __Version 1.11.0__, there is the new config value `MAKER_CHECK_INTERNET`.
If you wish to use your microservice, but got no internet at the moment, the data will be saved and send later.
One problem that occurred, is that, for example on a standard Raspberry Pi, the clock and therefore the timestamp will probably be wrong.
This new option tackles that. If it's set active with an active microservice, it will check for internet connection at startup.
If there is no connection, a dialog will pop up and give the user the possibility to adjust the time.
In case the machine got a RTC build in and uses it, this option can usually be set to `false`, because due to the RTC, the time should be correct.


## Ui Seems Wrong on none RaspOS System
On different Linux systems (other than the recommended Raspbian OS), there may be differences in the look and functionality of the user interface.
This can be dependant on the flavour of Linux, as well as the desktop variant you are using.
I had best experience when using a LXDE/XFCE variant, for example of a Debian Linux, on a none Raspberry Pi single board computer.
Other desktop variants may do not respect the always on top property, resulting in the taskbar show up on top the app when running the program and pop ups appear.
Please take note that CocktailBerry will run on other systems than the Raspberry Pi OS and RPi, but may take some tweaking and testing in the settings.
Since I probably don't own that combination of Hardware and OS, you probably need to figure out that settings by yourself.
If you are a unexperienced user with Linux, I recommend you stick to the recommended settings on a Pi.

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
sudo python3 main.py
```

```bash
#!/bin/bash
# launcher.sh for CocktailBerry
cd /home/pi/CocktailBerry/
python3 runme.py
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

**By the way**: The provided installer script does all that steps for you.

### The GUI on the RPi Looks Different from the Screenshots

I've noticed when running as root (sudo python3) and running as the pi user (python3) by default the pi will use different GUI resources.
Using the pi user will result in the shown interfaces at CocktailBerry (and the program should work without root privilege).
Setting the XDG_RUNTIME_DIR to use the qt5ct plugin may also work but is untested.

### Some Python Things do not Work

Older Raspberry Pi OS version (older than _November 2021_) still deliver Python 2.
Since Raspberry Pi OS Bullseye version (based on Debian 11) Python 3 is the default version if you type `python` or `pip`.
Typing `python --version` or `pip --version` will show your version of Python.
If it's still Python 2, consider upgrading your OS or check `python3 --version` and use the `pip3` as well as the `python3` command instead the usual ones.
