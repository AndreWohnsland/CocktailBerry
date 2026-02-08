# Installation

Here you can find all the requirements and installation steps.

## Prerequisites

These are the minimal tools needed to get started:

- [uv](https://docs.astral.sh/uv/getting-started/installation/) or [Python 3.13+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- recommended: **latest** [Raspberry Pi OS, 64 bit](https://www.raspberrypi.com/software/) (Desktop, Trixie)

The desktop version of Raspberry Pi OS is recommended, but if you just want to have a peak into the project, any OS having Python and Git will work just fine.
The RPi is needed to control the Pumps in a real machine, but the program will work fine even without any physical machine.

## Install CocktailBerry on the RPi

After flashing the latest Raspberry Pi 64 bit OS, you can use the provided shell scripts to set everything automatically up on your Raspberry Pi.
Or just install [the requirements](#installing-requirements), when you want to have a look into the program on your PC.
You can always install the other things later, the docs provide information within each according section.

### Automatic Installation

!!! tip "RPi: Try the new all in one Script"
    If you are on your Raspberry Pi, you can now also use the so called *All In One Script*!
    This will check that git, Python and your OS are compatible for the project and install CocktailBerry including Docker and compose on the Pi.
    
    Just use:

    ```bash
    wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash
    ```
    to get the script and run it on the Pi. To easy to be true, isn't it?

If you want to have the new v2 API and app, see [web setup](web.md) how to easily switch after the setup.
Or add a `-s v2` at the end of the command to execute the switch directly after installing.

### Manual Installation

To clone and setup this project run:

```bash
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd ~/CocktailBerry
# Setup for the RPi
# Docker is optional but needed for some cool extra features
sh scripts/install_docker.sh
sh scripts/install_compose.sh
# This will set up everything important on your RPi
cd ~/CocktailBerry
sh scripts/setup.sh
# now we are good to go
uv run runme.py # (1)!
```

1. add `--extra v1` or `--extra nfc` to the `uv run` command, if you want to have v1 support or NFC support.

!!! note "This Should be All"
    As long as you are on the recommended Raspberry Pi + OS, this should be all you need to execute for a complete setup.
    This provided script will probably not properly work on other systems, since each OS may handle things differently.
    If you are on another system, have a look into the other instructions, [faq](faq.md) or [troubleshooting](troubleshooting.md).

## Installing Requirements

On none Pi systems, the best way is to use [uv](https://docs.astral.sh/uv/getting-started/installation/).
You just need to clone the project and navigate into the folder.
If uv is installed, just run:

```bash
uv sync # add --extra v1 for v1 requirements or --extra nfc for nfc support
```

to get all requirements.

## Install PyQt6 on RaspberryPi

On the latest Raspberry Pi OS (Trixie), PyQt6 installs automatically via uv when you run `uv sync --extra v1`.
If you encounter issues, you can install the system package as fallback:

```bash
sudo apt update
sudo apt install python3-pyqt6
```

## Development on Non-Pi Hardware

When you are working on another hardware (for example on a Windows or macOS engine) it is recommended (but not necessary) to set `UI_DEVENVIRONMENT` to `true`.
This will enable your cursor.
All configuration can be customized under `custom_config.yaml`, or over the user interface of the program.
This file will be created at the first program start.

## Touchscreen settings

It's worth mentioning that the UI is optimized for a touch display with a 800x480 or a 1024x600 resolution.
By default, the full screen is also limited to 800x480.
So usually, you won't have any problems with the usual HD or uHD screens.
You can change the application size with the according config settings, if you want to use a different screen size.
See [Setting up the Machine / Modifying other Values](setup.md#setting-up-the-machine-modifying-other-values) for more information.
If you are using a high resolution screen, I recommend [this solution](troubleshooting.md#using-a-high-resolution-screen) to prevent the UI looking weird.
