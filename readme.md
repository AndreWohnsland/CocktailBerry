# The Cocktailmaker

#### A Python and Qt Based App for a Cocktail machine

<br />

<!-- TOC -->

- [The Cocktailmaker](#the-cocktailmaker)
- [Overview](#overview)
  - [Machine](#machine)
  - [Interface](#interface)
- [Installing Requirements](#installing-requirements)
  - [Minimal Requirements](#minimal-requirements)
  - [Install PyQt5 on RaspberryPi](#install-pyqt5-on-raspberrypi)
  - [Install PyQt5 on other Systems](#install-pyqt5-on-other-systems)
  - [Development on Non-Pi Hardware](#development-on-non-pi-hardware)
- [Setting up the Maker](#setting-up-the-maker)
  - [Adding new Recipes or Ingredients](#adding-new-recipes-or-ingredients)
  - [Setting up the Machine / Modifying other Values](#setting-up-the-machine--modifying-other-values)
- [Troubleshooting](#troubleshooting)
  - [Problems while Running the Program](#problems-while-running-the-program)
  - [Touchscreen Calibration](#touchscreen-calibration)
  - [Problems Installing Software on Raspberry Pi](#problems-installing-software-on-raspberry-pi)
    - [PyQt can't be Installed](#pyqt-cant-be-installed)
    - [Numpy Import Error at Matplotlib Import](#numpy-import-error-at-matplotlib-import)
    - [How to get the GUI Running on Startup](#how-to-get-the-gui-running-on-startup)
    - [The GUI on the RPi Looks Different than on the Screenshots](#the-gui-on-the-rpi-looks-different-than-on-the-screenshots)
- [Advanced Topics](#advanced-topics)
  - [Microservices](#microservices)
  - [Dashboard with Teams](#dashboard-with-teams)
  - [Usage of Services](#usage-of-services)
  - [Installing Docker](#installing-docker)
- [Development](#development)
  - [Program Schema](#program-schema)
  - [Pull Requests and Issues](#pull-requests-and-issues)
- [Side Notes](#side-notes)
- [ToDos](#todos)

<!-- /TOC -->

<br />

# Overview

Hello everyone, I am proud to announce the first iteration of the refactored code of the Cocktailmaker and the resulting 1.0 release after roughly one year of operating the machine in real life.
I am _Andre Wohnsland_, a German System Engineer in IoT, trying to get better in Python every day. This is was originally my first published project, a RaspberryPi app for a custom designed Cocktailmaker also made by me.

Some impressions of the UI can be found [here](https://imgur.com/a/fbZ0WuS) and of the machine [here](https://imgur.com/a/Z4tfISx). This app is currently under further construction, new features and refactoring of the old codebase takes place. If you got any questions or proposed improvements, feel free to share them by contacting me.

This app is used to control a cocktail machine and prepare easily cocktails over a nice-looking user interface. It also offers the option to create and manage your recipes and ingredients over the interface and calculates the possible cocktails to prepare over given ingredients.

## Machine

The Machine consists out of a Raspberry Pi + touchscreen, 5V relays as well as membrane pumps, cabeling and a custom design housing made out of bended, laser cut and welded stainless steel. The electronics are hidden in a water proof housing, the pumps are within the casing.

In Action:

<img src="docs/pictures/Cocktailmaker_action.gif" alt="Cocktail in the making" width="400"/>

Frontview:

<img src="docs/pictures/Frontview.jpg" alt="Frontview" width="600"/>

Sideview:

<img src="docs/pictures/Sideview.jpg" alt="Sideview" width="600"/>

## Interface

The interface was programmed with PyQt5 for the users to easily interact with the maker and enter new ingredients/recipes. There are different views for the tasks.

The Maker GUI:

<img src="docs/pictures/Main_ui.png" alt="Maker" width="600"/>

The Ingredient GUI:

<img src="docs/pictures/Ingredients_ui.png" alt="Ingredient" width="600"/>

The Recipe GUI:

<img src="docs/pictures/Recipes_ui.png" alt="Recipe" width="600"/>

The Bottle GUI:

<img src="docs/pictures/Bottles_ui.png" alt="Bottle" width="600"/>

# Installing Requirements

## Minimal Requirements

Disclaimer: since the adding of the new `requirements.txt` file it should also be possible just to run `pip install -r requirements.txt` in the folder to get all requirements.

```
- Python 3.6
- PyQt5
- RaspberryPi 3 (older may work but are not tested)
```

It's worth mentioning that I optimized the UI for a touch display with a 800x480 resolution ([this is my display](https://www.amazon.de/gp/product/B071XT9Z7H/ref=ppx_yo_dt_b_asin_title_o05_s00?ie=UTF8&psc=1)). On the code, the full screen is also limited to these dimensions. So usually you won't have any problems with the usual HD or uHD screens. But some screens (like my little 13' Laptop screen) don't show the proper fonts/UI placements. If you are planning to use a touch screen of another resolution for the machine you may consider changing `w.setFixedSize(800, 480)` in the `runme.py` to your dimensions or even rework the UI-file a little bit.

## Install PyQt5 on RaspberryPi

You will need at least PyQt5 on your RaspberryPi. More information can be found at [riverbank](https://riverbankcomputing.com/software/pyqt/intro).\
To install PyQt5 on your Pi run:

```
sudo apt-get update
sudo apt-get install qt5-default pyqt5-dev pyqt5-dev-tools
```

## Install PyQt5 on other Systems

If you want to run some testing on other systems, you can get PyQt5 [here](https://www.riverbankcomputing.com/software/pyqt/download5).\
As long as you are using a supported version of Python you can install PyQt5 from [PyPi](https://pypi.org/project/PyQt5/) by running:

```
pip3 install PyQt5
```

## Development on Non-Pi Hardware

When you are working on another hardware (for example on a Windows or macOS engine) it is recommended (but not necessary) to set `DEVENVIRONMENT` to `True`. This will enable your cursor for example. All configuration can be set under `config/config_manager.py`:

```python
DEVENVIRONMENT = True
```

This include the password (if needed/wanted), the configuration and physical connections of your hardware (like GPIO pin connection and pump volume), the names of the logger and restricted access to some tabs.

# Setting up the Maker

## Adding new Recipes or Ingredients

There are only limited ingredients and recipes. But you can add your own data to the program as well.
This app uses a sqlite3 Database coupled to the UI. So, it's quite easy to implement new ingredients or even recipes.
Just use the implemented UI for the procedure under the according tabs (**Zutaten** (ingredients) or **Rezepte** (recipes)).

All entered values are checked for reason and if something is wrong, an error message will inform the user what is wrong with the data input. If you want to browse through the DB I recommend some program like [DB Browser for sqlite](https://sqlitebrowser.org/).

## Setting up the Machine / Modifying other Values

These values are stored under the `config/config_manager.py` file. Depending on your pumps and connection to the Pi, these can differ from mine and can be changed:

- `MASTERPASSWORD` I recommend a string of pure numbers, since the UI supports only numbers with a build in numpad window
- `USEDPINS` are the RPi-Pins where each Pump is connected
- `PUMP_VOLUMEFLOW` is the according volume flow for each pump in ml/s
- `NUMBER_BOTTLES` are the number of supported bottles. Currently the Ui is build for up to ten bottles
- `CLEAN_TIME` is the time the machine will execute the cleaning program
- `SLEEP_TIME` is the sleep interval between each Ui refresh and check of conditions while generating a cocktail
- `PARTYMODE` en- or disables the recipe tab (to prevent user interaction)
- `LOGGERNAME` name for the standard logger
- `LOGGERNAME_DEBUG` name for the error logger
- `USE_MICROSERVICE` boolean flag to post to microservice set up by docker (optional)
- `MICROSERVICE_BASE_URL` base url for microservice (if default docker it is at http://127.0.0.1:5000)
- `USE_TEAMS` boolean flag to use teams feature (version >= 1.2) (optional)
- `TEAM_BUTTON_NAMES` List of format ["Team1", "Team2"] (optional)
- `TEAM_API_URL` Endpoint of teams API, default used port by API is 8080
- `DEVENVIRONMENT` boolean flag to enable some development features

In addition, there is a `Shared` config class, with dynamic values. The only thing you may want to change is `supress_error` to true, this will activate a wrapper function catching and logging errors of the wrapped function. In production this will effectively prevent the app from crashing due to errors (bugs) and log them, but setting it to `True` is at own risk.

Depending on your preferred use, these values can differ. Then just run `runme.py`.

Setting up the machine is quite easy as well. Just go to the **Belegung** Tab and select via the dropdown boxes your assigned ingredients. In addition, you can define ingredients which are also there, but are not connected to the machine (under _Zutaten/Ingredients > verfügbar/available_). You can define ingredients in recipes (at _selbst hinzufügen / add your own_) which should be later added via hand (for example sticky ingredients which would not be optimal for your pump, or only very rarely used ones in cocktails).

The program will then evaluate which recipe meets all requirements to only show the recipes where even the ingredients added via hand later are available and the recipe will be shown in the **_Maker_** Tab.

# Troubleshooting

## Problems while Running the Program

All cases (e.g. not enough of one ingredient, no/wrong values ...) should be handled and a info message should be displayed.\
If in any case any unexpected behavior occurs feel free to open an issue. Usually a part of the actions are also logged into the logfiles.

## Touchscreen Calibration

Sometimes you need to calibrate your touchscreen, otherwise the touched points and cursor are out of sync. First you need to get and compile xinput. After that, you can execute the program and select the crosses on the touchscreen according to the shown order.

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

To adjust those new touch coordinates, they need to be saved. The xinput programm should print out some block beginning with `Section "InputClass"` and ending with `EndSection`. This part needs to be entered in the `99-calibration.conf`.

```bash
sudo mkdir /etc/X11/xorg.conf.d
sudo nano /etc/X11/xorg.conf.d/99-calibration.conf
```

After the reboot, the calibration should be okay.

## Problems Installing Software on Raspberry Pi

The Raspberry Pi can sometimes differ from other machines in term of installation. Here are some issues that might occur.

### PyQt can't be Installed

You probably need to run `sudo apt install python3-pyqt5` instead of `pip install pyqt5` on the pi

### Numpy Import Error at Matplotlib Import

Try first running `pip3 install -U numpy` and `sudo apt install libatlas3-base`. If it is still not fixed, try uninstalling and installing numpy / matplotlib again. If really nothing else works try `sudo pip3 install -U numpy`, then you will probably need to run the python file with root priviledge as well, which may result in another GUI style used by the system.

### How to get the GUI Running on Startup

I found the easiest thing is to use RPis Autostart. Create a .desktop file with `sudo nano /etc/xdg/autostart/cocktail.desktop` and the `launcher.sh` in your `/home/pi` folder:

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
sudo python3 /home/pi/Cocktailmaker_AW/dashboard/qt-app/main.py
```

```bash
#!/bin/bash
# launcher.sh for cocktailmaker
python3 /home/pi/Cocktailmaker_AW/runme.py
```

If your setup is equal to mine (Raspberry Pi, Maker GitHub cloned to `/home/pi/` folder) you can also just copy the files and comment/uncomment within the launcher.sh to save some typing:

```bash
cp /home/pi/Cocktailmaker_AW/launcher.sh /home/pi/
cp /home/pi/Cocktailmaker_AW/cocktail.desktop /etc/xdg/autostart/
```

If there are any problems with the lxterminal window opening and instant closing, check the rights of the shell file, it needs executable (x) rights, otherwise use `chmod` to give x-rights:

```bash
sudo chmod +x /home/pi/launcher.sh
# or
sudo chmod 755 /home/pi/launcher.sh
```

### The GUI on the RPi Looks Different than on the Screenshots

I've noticed when running as root (sudo python3) and running as the pi user (python3) by default the pi will use different GUI ressources. Using the pi user will result in the shown interfaces at the cocktailmaker (and the program should work without root privilege). Setting the XDG_RUNTIME_DIR to use the qt5ct plugin may also work but is untested.

# Advanced Topics

## Microservices

As an further addition there is the option to run a microservice within docker which handles some networking topics.
Currently this is limited to:

- Posting the cocktailname, used volume and current time to a given webhook
- Posting the export csv as email to a receiver

The separation was made here that a service class within the cocktailmaker needs only to make a request to the microservice endpoint. Therefore all logic is separated to the service, also there is no need for multiple worker to not block the thread when the webhook endpoint is not up (Which would result in a delay of the display without multithredding). In the future, new services can be added easily to the docker container to execute different tasks. One example of the usage [can be found in my blog](https://andrewohnsland.github.io/blog/cocktail-maker-now-with-home-assistant).

## Dashboard with Teams

With `version 1.2`, there is a team feature implemented into the maker. If enabled within the config, the user can choose one of two teams to book the cocktail and according volume to. The names of the teams, as well the URL of the dashboard device can be specified within the config. The cocktailmaker will then send the information to the Teams API. The Dashboard will use the API to display the current status in either amount of cocktails or volume of cocktails per team. In addition, there is the option to display all time data of the leaderboard. By default, the latest 24 hours, so mostly this party, will be shown. You should use a second device for the api / the dashboard for easy display on another screen.

<img src="docs/pictures/teams_ui.png" alt="Maker" width="600"/>

<img src="docs/pictures/dashboard.png" alt="Maker" width="600"/>

The recommended way to to is to use a second Raspberry Pi with a touchscreen attached. Then build the docker-compose file and execute the `dashboard/qt-app/main.py`. In before you should instal the `requirements.txt` within the same folder using pip. See `Usage of Services` how to setup docker-compose in general.

A second option is to use the `docker-compose.both.yaml` file with the compose `--file` option. This will build up the backend API, as well as a Streamlit frontend Web App. Streamlit is using pyarrow, which the Raspberry Pi 3 (Armv7 Architecture) seems not be able to build without any tweaks. On other architectures (like x86) the container could be build without any problems. If theses things confuse you, I strongly recommend using the first recommended option, since you only will loose the possibility to access the dashboard with multiple devices, like a smartphone.

## Usage of Services

Simply have `docker-compose` installed and run the command in the main folder for the cocktailmaker microservice or in the dashboard folder (on another device) for the dashboard service:

```
docker-compose up -d
```

This will handle the setup of all docker services. You will have to rename the `.env.example` file to `.env` and enter the needed secrets there for the container to work fully.

## Installing Docker

tl;dr: Just run these commands in sequence on the pi and reboot after the first half.

```bash
sudo apt-get update && sudo apt-get upgrade
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker ${USER}
# reboot here
sudo apt-get install libffi-dev libssl-dev
sudo pip3 install docker-compose
sudo systemctl enable docker
# tesing if it works
docker run hello-world
```

# Development

## Program Schema

In the following diagram, the schema and Classes / Containers are displayed in a simplified version.

![ProgramSchema](docs/diagrams/out/ProgramSchema.svg)

## Pull Requests and Issues

If you want to support this project, feel free to fork it and create your own pull request. If you run into any issues, feel free to open a ticket / issue.

# Side Notes

As you probably noticed, the interface is in German since this is the native language of all my friends (which are the users of the machine). I am planning to translate all text to English at some point, and give the possibility to choose between both languages, but currently there is no planned date for that.

To achieve this goal the message display structure needs to be restructured.

# ToDos

- Convert from basic sqlite to SQLAlchemy
