# CocktailBerry Web

!!! info "Not the default interface yet"
    The web interface is stable, but v1 (the Qt app) is still the default.
    If you spot any issues, please report them in the [GitHub repository](https://github.com/AndreWohnsland/CocktailBerry/issues/new/choose).
    In general, most features should work as expected, but there might be some edge cases that are not covered yet.

This is within the [roadmap](https://github.com/users/AndreWohnsland/projects/1) for v2.
The goal of this release is to provide a more polished and at the same time more flexible app.
It includes a new web interface that can be used to control the machine from any device on the same network.
This allows users to control the machine from their phone, tablet, or any other device that has a web browser.
Machines without a display (e.g. Headless) are no longer a dream, you can build and use them now with CocktailBerry.
In addition, the API (backend) is no longer tightly coupled to the frontend.
Advanced users can use the API for their own use, like writing their own frontend or automating tasks via home automation.

## Quick Install

You can also directly install it via the all-in-one installer script by specifying `v2` as version.

```bash
wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash -s v2
```

This will do similar setup steps as in v1, but directly install the web interface version.

## Requirements

It is not recommended to use this on Raspberry Pi 3 series or older, as the performance might not be sufficient.
Use a Raspberry Pi 4 with 2 GB or more of RAM for the best experience.
You need to have an up-to-date Raspberry Pi OS installed.
The web interface requires a modern web browser that supports the latest web technologies.
You do not need a touch screen, just a device being able to connect to the same network as the Raspberry Pi.
However, a touchscreen can be used to control the app directly on the Raspberry Pi.

## Limitations

*This is for the v2 web interface. For the v1 (Qt) UI, see [Touchscreen settings](installation.md#touchscreen-settings).*

Currently, the web interface might have some issues with touch screens directly connected to the Raspberry Pi.
In some occasions, older OS or not properly configured screens, the default keyboard might not show up.
If you are using an external device to control the app, this should not be an issue.
In case you are using a touch screen directly connected to the Raspberry Pi, running the browser in non-kiosk mode might help.
There is also the option in the software to enable a web keyboard instead.
This should work in fullscreen.

## Installation

The easiest way to use the new interface is to use the CocktailBerry CLI [setup-web command](commands.md#switch-to-cocktailberry-web), if you installed CocktailBerry the usual way.
Existing installations should update to at least version v2.0.0 to have this command available.
Or you can use the v2 flag in the all-in-one installer script [as shown above](#quick-install).

!!! warning "Before starting"
    Before you start the update, make sure to backup your data.
    The update should not delete any data, but it is always better to be safe than sorry.
    It is also recommended to have an up-to-date operating system.
    If you installed CocktailBerry a long time ago, please do a clean install instead of updating.

```bash
cd ~/CocktailBerry
# optional with --ssl to enable https
uv run runme.py setup-web
```

This will set up the web interface as the default interface and start it instead of the old main program.
You can now access the website by opening your browser and navigating to `http://<ip>` or locally on `http://localhost`.

Note: from here on, on a v2 install, use `uv run api.py` instead of `uv run runme.py`.

## RPi Virtual Keyboard

The Raspberry Pi OS has a virtual keyboard that can be enabled via raspi-config.
In case you do not want it, and it is activated, see the section below to disable it.
If it should not show up when clicking on an input field, you can try to enable it manually.

```bash
cd ~/CocktailBerry
uv run api.py add-virtual-keyboard
```

## Disable the Virtual Keyboard

If you enabled it via the command above and want to disable it again, you can do so by running the following command.

```bash
cd ~/CocktailBerry
uv run api.py remove-virtual-keyboard
```

In case you have not enabled it via the command above, you can also disable it via raspi-config.

```bash
sudo raspi-config
```

Then go to `Display Options` -> `On-Screen Keyboard` and disable it.

## Rollback to Qt

If you want to go back to the old interface, you can do so by running the following command.

```bash
cd ~/CocktailBerry
uv run api.py switch-back
```
