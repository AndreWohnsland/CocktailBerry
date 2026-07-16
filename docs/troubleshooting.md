---
icon: material/bug-outline
tags: [Help]
---

# Troubleshooting

If you run into any problems, check here first for a solution.
Please ensure that you are running the latest 64 bit Raspberry Pi OS and CocktailBerry version.
If you don't find any solution here, you can [open a ticket](https://github.com/AndreWohnsland/CocktailBerry/issues/new/choose).

## Major Version Updates

When a major version of CocktailBerry is released, see the [Migration Guides](migration/index.md) for upgrade steps.

## Problems while Running the Program

All cases (e.g. not enough of one ingredient, no/wrong values ...) should be handled, and an info message should be displayed.
If in any case any unexpected behavior occurs, feel free to open an issue.
Usually, part of the actions is also logged into the log files.
When submitting an error, please also provide the `logs/debuglog.log` file.

## Icons are Missing

If some of the icons (check / cross on the checkbox, up / down arrow on the list view) are missing, make sure you run the script within the folder (e.g. `uv run runme.py`) and not from another folder (e.g. `CocktailBerry/runme.py`).
This is because of the nature of Qt and the translation to python, if you go from another folder the picture resources can't be found.

Another reason may be if you are using a custom style sheet with colors using rgb.
If that's the case, please change the color codes to the hexadecimal representation of the color, because qtawesome can't handle rgb color codes.

## Changing Volume Unit

For the users of the machine, there is the possibility to set the `EXP_MAKER_UNIT` and `EXP_MAKER_FACTOR` options to change the displayed unit, for example to oz.
Please note that the units stored in the database are still in ml, and if inserting new recipes, you still need to provide them in ml.
This feature is purely cosmetic and for the user of the maker tab when making cocktails, so that no calculations need to be done while making cocktails.

## Restoring Database

The migrations create a backup of the database before doing the modifying steps.
If you'd rather not have the new recipes, you can overwrite the local `Cocktail_database.db` with the `Cocktail_database_backup.db` file.

```bash
cp Cocktail_database_backup-{your-date-string}.db Cocktail_database.db
```

This will restore the state of the backup prior to this migration step.
Please take a look at the production_log file, if a backup was created.
Otherwise, you may end up using an older one.

## Using a High Resolution Screen

The UI of the program is somewhat dynamic, but Qt has its limitations.
To ensure that the UI looks nice like in the screenshots, a resolution not higher than ~1200px on the long side (width) is recommended.
If you happen to use a high-resolution screen, there is an easy fix, though.
For example, when using a screen with a 2560x1600 resolution, I would recommend dividing the value by `x` (for example x=2).
In the CocktailBerry config, set width to 2560/2 = 1280 and height to 1600/2 = 800.
In case you used the provided setup, change the first line `export QT_SCALE_FACTOR=1` from 1 to x (2 in the example case) in the `~/launcher.sh` file.
Note that `~/launcher.sh` is a symlink to a git-tracked file, so replace it with your own copy first, otherwise an update overwrites the change (see [CLI Commands](commands.md) for the steps).
This will use the lower dimensions for the application but scale it up by the factor of two so it occupies the whole screen.
Decimal numbers for x also work, just try not to get decimals for width / height.
If you use your own startup script or similar, just add the export line with a corresponding value to it, or set the environment variable in any other desired way.

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
If you wish to use your microservice, but have no internet at the moment, the data will be saved and sent later.
One problem that occurred, is that, for example on a standard Raspberry Pi, the clock and therefore the timestamp will probably be wrong.
This new option tackles that. If it's set to active with an active microservice, it will check for internet connection at startup.
If there is no connection, a dialog will pop up and allow the user to adjust the time.
In case the machine has an RTC built in and uses it, this option can usually be set to `false`, because due to the RTC, the time should be correct.

## Get the LED Working

*See also: [Implementing LEDs](faq.md#implementing-leds) for what the LED feature does.*

WS281x LEDs can be driven two ways, picked automatically from the **pin** you set in the WSLED config:

- **SPI — pin `10` (recommended).**
  Needs no root, and it is the **only** option that works on the **Raspberry Pi 5**.
  Also works on the Pi 3/4.
  Jump to [Run the LEDs without sudo](#run-the-leds-without-sudo-spi-also-works-on-pi-5).
- **PWM/PCM — pins `12`/`18` (PWM) or `21` (PCM).**
  Uses the `rpi_ws281x` library, requires running as **root**, and works on the **Pi 0–4 only** (the driver does not run on the Pi 5).
  Described next.

### PWM/PCM route (Pi 0–4, needs root)

Getting the WS281x to work this way may be a little bit tricky.
You need to run the program as root/sudo, so you also need to change this in `~/launcher.sh`.
`~/launcher.sh` is a symlink to a git-tracked file, so replace it with your own copy first, otherwise an update overwrites the change (see [CLI Commands](commands.md) for the steps).
If you are using the latest installer, there will be a virtual environment created, so you should use this as root.

```bash
# for v1: change this line
# uv run --extra v1 --extra nfc runme.py
# into:
uv sync --inexact --extra v1 --extra nfc
sudo -E .venv/bin/python runme.py
# for v2: change this line
# uv run --extra nfc api.py
# into:
uv sync --inexact --extra nfc
sudo -E .venv/bin/python api.py
```

If the GUI looks different than when you run it without sudo, try the `-E` flag, this should use your environment for Qt.

See [here](https://github.com/jgarff/rpi_ws281x#gpio-usage) for a possible list and explanation for GPIOs.
I had success using the 12 and 18 PWM0 pins, while also disabling (use a # for comment) the line `#dtparam=audio=on` on `/boot/config.txt`.
Other described pins may also work, but are untested, so I recommend sticking to the two that should work.
If you use any other non controllable LED connected over the relay, you can use any pin you want, since it's only activating the relay.

### Run the LEDs without sudo (SPI, also works on Pi 5)

The `sudo` above is only needed because the PWM/DMA driver pokes `/dev/mem`.
If you instead drive the WS281x over **SPI**, no root is required — and SPI is the **only** way that works on the Pi 5 (the old PWM/DMA driver does not run there at all).

Over SPI, CocktailBerry uses its own small `spidev`-based driver (not `rpi_ws281x`), selected automatically when the pin is `10`.
You only change the pin and do a one-time setup:

- Set the LED **Pin to `10`** in the CocktailBerry config (WSLED entry).
  Wire the LED `DIN` to **GPIO10 / physical pin 19** (SPI0 MOSI).
- Enable SPI and add your user to the `spi` group.
  The installer (`scripts/setup.sh`) already does this; to do it manually:

```bash
sudo raspi-config nonint do_spi 0
sudo usermod -aG spi "$(whoami)"
sudo reboot
```

After that you can run CocktailBerry normally — no `sudo`, no edits to `~/launcher.sh`.

If the LEDs flicker or show wrong colours over SPI (common on long strips), the SPI clock/buffer needs tuning.
Add to `/boot/firmware/config.txt` (older Pi OS: `/boot/config.txt`):

```
core_freq=250
core_freq_min=500
```

and append `spidev.bufsiz=32768` to `/boot/firmware/cmdline.txt` (keep it one single line, space-separated), then reboot.
Check it took effect with `cat /sys/module/spidev/parameters/bufsiz` (should print `32768`).

## Set Up RFID Reader

Setting up a GPIO RFID reader and integrating it into the program is an intermediate task.
It is not recommended for complete beginners, and it may include some tinkering.
As long as you use the recommended usb reader, you should be fine.
Currently, you can use these different types of readers:

- Basic {{ extra.mfrc522_link }} (SPI Protocol)
- {{ extra.rfid_reader_link }} (only reading UID supported)

!!! bug "Please Read"
    Reading / Writing RFIDs while still having an interactive GUI may cause a lot of trouble.
    Some reader frameworks lock themselves until the read or write is done and have no direct cancel methods.
    So even using threads only fixes the responsiveness of the app.
    Therefore, it's best to trigger a write, finish the write.
    If you have experience with the reader + Python feel free to contact me, so we can improve this feature.

Setting them up is described [here for the MFRC522](https://pimylifeup.com/raspberry-pi-rfid-rc522/).
You only need the wiring and the installation of the libraries (usually they are already installed).
The corresponding code is integrated into CocktailBerry.
After that, you select the corresponding option in the settings dropdown for the reader.
When using the teams function, you can then also use an RFID chip, which inserts the information (name of person) for the leaderboard.
In addition, when going to the settings tab, the option to write a string (name) to a chip is enabled.

Take care that you don't use any of the connected pins of the RFID reader in the CocktailBerry config for a pump or an LED.
If you do so, remove them or replace them with another pin.
Otherwise, the RFID will not work.
It's best to restart the Pi afterwards and then check if the RFID is working as intended.
While the USB NFC reader does not occupy any GPIO pins, it has some challenges on its own.
You currently can't write data to the card, only reading the UID is supported.

## UI Seems Wrong on non-RaspOS System

On different Linux systems (other than the recommended Raspberry Pi OS), there may be differences in the look and functionality of the user interface.
This can be dependent on the flavour of Linux, as well as the desktop variant you are using.
I had the best experience when using a LXDE/XFCE variant, for example of a Debian Linux, on a non-Raspberry Pi single board computer.
Other desktop variants may not respect the always on top property, resulting in the taskbar showing up on top of the app when running the program and pop ups appear.
Please note that CocktailBerry will run on other systems than the Raspberry Pi OS and RPi, but may take some tweaking and testing in the settings.
Since I probably don't own that combination of hardware and OS, you probably need to figure out those settings by yourself.
If you are an inexperienced user with Linux, I recommend you stick to the recommended settings on a Pi.

## Task Bar Overlap / Push GUI

This may happen (especially at older versions of RPi OS or higher res screens) when running the program and some dialog window opens.
The task bar (bar with programs on it) may overlap the dialog window or push it down by its height.
Ensure that you have unchecked the "Reserve space, and not covered by maximised windows" option.
You can find it under the panel preferences (right click the task bar > panel settings > Advanced).
Unchecking this box usually fixes this problem.

## Reset Config

In case you want to reset the configuration, it is the best way to just delete the custom_config.yaml in the main folder.
This file holds your configuration and will be created with the defaults if it does not exist.

There are also backups of the config file before migration, located at `~/cb_backup/` with the version number before this specific migration.
The config file is located at `~/CocktailBerry/custom_config.yaml`.
You can open it with any text editor.
Or just use the terminal:

```bash
cd ~/CocktailBerry
sudo nano custom_config.yaml
# use the arrow keys to navigate
# ctrl + o to save
# ctrl + x to exit

# or see what was your old config values in case something went wrong
cat ~/cb_backup/custom_config_pre_{version_number}.yaml
```

## Software does not Update

*See also: [How to get Updates](faq.md#how-to-get-updates) and the [`MAKER_SEARCH_UPDATES` setting](setup.md#updates).*

It may happen that you don't get the latest version of the software prompted at start, even if you check for updates.
This can be due to different reasons.
First, check if you have an internet connection.
If you have, check if you have the latest recommended version of python installed.
CocktailBerry will not show the update if the future required Python version is higher than the current installed one.
Another reason may be that your git file is corrupted.
Check for errors like object file x is empty:

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

## Update Fails with "dubious ownership" (running as root)

If you run CocktailBerry as root (e.g. for PWM LEDs, see [Get the LED Working](#get-the-led-working)) the updater may fail with:

```text
fatal: detected dubious ownership in repository at '/home/cocktailberry/CocktailBerry'
```

This is a git safety check: the repository is owned by your normal user, but git is now running as root.
Mark the repo as safe at the system level (read by every user, including root):

```bash
sudo git config --system safe.directory "$HOME/CocktailBerry"
```

The latest installer (`scripts/setup.sh`) already does this for you.

## Problems with Cocktail Pictures

With the v1.30.0 release, the maker view was completely rewritten.
This includes the way cocktails are shown as a list and single view.
There is a picture now for every cocktail, the default provided cocktails all got a corresponding picture.
There is also a default picture for cocktails without a picture, like newly user added ones.
You can upload your own pictures via the corresponding button in the recipe tab.
Your picture will then replace the default provided picture.

The user pictures are stored in the `~/CocktailBerry/display_images_user` folder.
The picture will be saved with the cocktail id as name and jpg format.
If you prefer to add pictures manually in that folder instead of the GUI, name the file with the cocktail id (e.g. `5.jpg`).

If your database is quite old, newer cocktails you added may either have the default picture, or may have another picture from new cocktails contained now in the database.
This is due to the database using incrementing integers as primary key for the cocktails.
This is historical and can't be changed easily in running installations.
If that's the case, please use the GUI option to replace wrong pictures with your desired ones.
If you feel that the default pictures are switched, you can also use the default ones as replacement.
They are located at `~/CocktailBerry/default_cocktail_images`.

Here is an extensive list of all default cocktails and their corresponding image.
If you think your cocktail has the wrong picture, you can use the corresponding picture name from the list below to replace it.

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

You probably need to run `sudo apt install python3-pyqt6` on the Pi.
This should usually not be an issue anymore when using uv and Trixie Raspberry Pi OS or later.

### How to get the GUI Running on Startup

The easiest thing is to use RPis Autostart.
Create a .desktop file with `sudo nano /etc/xdg/autostart/cocktail.desktop` and the `launcher.sh` in your `/home/pi` folder:

```text
[Desktop Entry]
Type=Application
Name=CocktailScreen
NoDisplay=false
Exec=/usr/bin/lxterminal -e /home/pi/launcher.sh
```

```bash
#!/bin/bash
# code to start the application, see v1-launcher.sh
```

If your setup is equal to the docs (Raspberry Pi, CocktailBerry GitHub cloned to the home folder) you can also just copy the files and comment/uncomment within the launcher.sh to save some typing:

```bash
cp ~/CocktailBerry/scripts/v1-launcher.sh ~/launcher.sh  # use v2-launcher.sh for v2
cp ~/CocktailBerry/scripts/cocktail.desktop /etc/xdg/autostart/
```

Copying to a real `~/launcher.sh` file (instead of the symlink the installer creates) means the file survives updates but does not receive their changes.

If there are any problems with the lxterminal window opening and instant closing, check the rights of the shell file, it needs executable (x) rights, otherwise use `chmod` to give x-rights:

```bash
sudo chmod +x ~/launcher.sh
# or
sudo chmod 755 ~/launcher.sh
```

!!! info "By the Way"
    The provided installer script does all those steps for you.

### The GUI on the RPi Looks Different from the Screenshots

I've noticed when running as root (sudo python) and running as the pi user (python) by default the pi will use different GUI resources.
Using the pi user will result in the shown interfaces at CocktailBerry (and the program should work without root privilege).
Setting the XDG_RUNTIME_DIR to use the qt5ct plugin may also work but is untested.
Using the user's environment with `sudo -E .venv/bin/python runme.py` should also do the trick.

### Raspberry Pi 5 GPIO Issues

The Raspberry Pi 5 needs the lgpio library for GPIO access.
Current versions manage lgpio as a normal dependency, so the installer and the built-in updater handle it automatically.
If GPIO stopped working on an old installation (for example after a manual `uv sync`, which removes packages not managed by uv), the best fix is to update to the latest version.
To fix an old installation in place instead, run the following commands:

```bash
cd "$HOME/CocktailBerry/"
sudo apt install liblgpio-dev
uv pip install lgpio
uv run --extra v1 --extra nfc runme.py
```
