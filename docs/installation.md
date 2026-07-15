---
icon: material/rocket-launch-outline
tags: [Setup]
---

# Installation

Here you can find all the requirements and installation steps.

## Prerequisites

These are the minimal tools needed to get started:

- [uv](https://docs.astral.sh/uv/getting-started/installation/) or [Python 3.13+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- recommended: **latest** [Raspberry Pi OS, 64 bit](https://www.raspberrypi.com/software/) (Desktop, Trixie)
- *optional:* for a manual v2 (web) install: [Node.js](https://nodejs.org/en/download/) and [Yarn](https://yarnpkg.com/getting-started/install)

The desktop version of Raspberry Pi OS is recommended, but if you just want to have a peek into the project, any OS having Python and Git will work just fine.
The RPi is needed to control the pumps in a real machine, but the program will work fine even without any physical machine.

## Install CocktailBerry

After flashing the latest Raspberry Pi 64-bit OS, you can use the provided scripts to set everything up automatically on your Raspberry Pi.
Or just [run the program](#running-the-program) directly, when you want to have a look into it on your PC.
You can always install the other things later, the docs provide information within each corresponding section.

*Building a physical machine? See [Hardware](hardware.md) for the parts list first.*

### Automatic Installation

!!! tip "RPi: Use the all-in-one Script"
    If you are on your Raspberry Pi, you can just use the so-called *All-in-One Script*!
    This will check that git, Python and your OS are compatible for the project and install CocktailBerry including Docker and Compose on the Pi.

    Just use:

    ```bash
    wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash
    ```
    to get the script and run it on the Pi. Too easy to be true, isn't it?

If you want to have the new v2 API and app, see [web setup](web.md) for how to easily switch after the setup.
Or add a `-s v2` at the end of the command to execute the switch directly after installing.

After the installation, you can [set up](setup.md#setting-up-the-machine-modifying-other-values) your CocktailBerry and tweak the settings to your liking.

### Manual Installation

To clone the project, run the following commands in your terminal:

```bash
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd ~/CocktailBerry
```

Then you can install the requirements and set up the project with the following commands:

```bash
# Setup for the RPi
# Docker is optional but needed for some cool extra features
sh scripts/install_docker.sh
sh scripts/install_compose.sh
# This will set up everything important on your RPi
cd ~/CocktailBerry
sh scripts/setup.sh
# now we are good to go
uv run --extra v1 runme.py # (1)!
```

1. add `--extra nfc` to the `uv run` command, if you want to have NFC support, use `api.py` instead for v2.

!!! note "This Should be All"
    As long as you are on the recommended Raspberry Pi + OS, this should be all you need to execute for a complete setup.
    This script will likely not work properly on other systems, since each OS may handle things differently.
    If you are on another system, have a look into the other instructions, [faq](faq.md) or [troubleshooting](troubleshooting.md).

## Running the Program

The best way is to use [uv](https://docs.astral.sh/uv/getting-started/installation/).
Choose which version you want to install and run.
You need to have this project cloned and set up, as described in the [Manual Installation](#manual-installation) section.

### V1 (PyQt Application)

```bash
uv run --extra v1 runme.py
# if you also want NFC support (needs libnfc-dev installed), use:
uv run --extra v1 --extra nfc runme.py
```

### V2 (API and Web Client)

```bash
uv run api.py
# if you also want NFC support (needs libnfc-dev installed), use:
uv run --extra nfc api.py
```

The automatic installer builds and serves the web page for you.
On a manual install, you also need to start the web client:

```bash
cd ~/CocktailBerry/web_client
yarn install
yarn dev
```

## Development on Non-Pi Hardware

The project has a `pi-hardware` dependency group, which is installed by default and contains the Pi-specific hardware libraries.
You can add `--no-group pi-hardware` to the `uv run` (or `uv sync`) command to skip installing them on your system.
Most of them only install on Linux anyway, so this is mainly relevant on a non-Pi Linux machine.

When you are working on other hardware (for example on a Windows or macOS engine) it is recommended (but not necessary) to set `UI_DEVENVIRONMENT` to `true`.
This will enable your cursor.
All configuration can be customized under `custom_config.yaml`, or over the user interface of the program.
This file will be created at the first program start.

## Touchscreen settings

*This covers the v1 (Qt) UI. For the v2 web interface, see [Limitations](web.md#limitations).*

It's worth mentioning that the UI is optimized for a touch display with an 800x480 or a 1024x600 resolution.
By default, the full screen is also limited to 800x480.
So usually, you won't have any problems with the usual HD or uHD screens.
You can change the application size with the corresponding config settings, if you want to use a different screen size.
See [Setting up the Machine / Modifying other Values](setup.md#setting-up-the-machine-modifying-other-values) for more information.
If you are using a high resolution screen, I recommend [this solution](troubleshooting.md#using-a-high-resolution-screen) to prevent the UI from looking weird.
