# Installation

Here you can find all the requirements and installation steps. 

## Prerequisites

These are the minimal tools needed to get started:

- [Python 3.9](https://www.python.org/downloads/) or newer
- [Git](https://git-scm.com/downloads)
- recommended: **latest** [Raspberry Pi OS, 64 bit](https://www.raspberrypi.com/software/) (Desktop, Bullseye)

The desktop version of Raspberry Pi OS is recommended, but if you just want to have a peak into the project, any OS having Python and Git will work just fine.
The RPi is needed to control the Pumps in a real machine, but the program will work fine even without any physical machine.

## Install CocktailBerry

After flashing the latest Raspberry Pi 64 bit OS, you can use the provided shell scripts to set everything automatically up on your Raspberry Pi.
Or just install [the requirements](#installing-requirements), when you want to have a look into the program on your PC.
You can always install the other things later, the docs provide information within each according section.
To clone and setup this project run:

```bash
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd ~/CocktailBerry
# Setup for the RPi
# Docker is optional but needed for some cool extra features
sh scripts/install_docker.sh
# This will set up everything important on your RPi
cd ~/CocktailBerry
sh scripts/setup.sh
# now we are good to go
python3 runme.py # (1)!
```

1.  Newer systems may execute python instead of python3

## Installing Requirements
The best way is to use the provided `requirements.txt` file.
If Python is installed, just run: 

```bash
pip install -r requirements.txt
``` 

to get all requirements.
Optionally, you can install the single needed dependencies:

- PyQt5, requests, pyyaml, GitPython, typer, pyfiglet, qtawesome

## Install PyQt5 on RaspberryPi

The PyQt5 installation of pip will probably fail on your RaspberryPi. To install PyQt5 on your Pi run:

```
sudo apt-get update
sudo apt-get install qt5-default pyqt5-dev pyqt5-dev-tools
```

More information can be found at [riverbank](https://riverbankcomputing.com/software/pyqt/intro).

## Development on Non-Pi Hardware

When you are working on another hardware (for example on a Windows or macOS engine) it is recommended (but not necessary) to set `UI_DEVENVIRONMENT` to `true`.
This will enable your cursor.
All configuration can be customized under `custom_config.yaml`, or over the user interface of the program.
This file will be created at the first program start.

## Touchscreen settings

It's worth mentioning that I optimized the UI for a touch display with a 800x480 or a 1024x800 resolution.
By default, the full screen is also limited to 800x480.
So usually, you won't have any problems with the usual HD or uHD screens.
You can change the application size with the according config settings, if you want to use a different screen size.
See [Setting up the Machine / Modifying other Values](setup.md#setting-up-the-machine-modifying-other-values) for more information.
If you are using a high resolution screen, I recommend [this solution](troubleshooting.md#using-a-high-resolution-screen) to prevent the UI looking weird.
