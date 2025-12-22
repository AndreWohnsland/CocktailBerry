# CocktailBerry Web

!!! info "This is still new and not the default interface yet"
    This is a new implementation and not so much battle tested like the old interface.
    If you spot any issues, please report them in the [GitHub repository](https://github.com/AndreWohnsland/CocktailBerry/issues/new/choose).
    In general, most features should work as expected, but there might be some edge cases that are not covered yet.

This is within the [roadmap](https://github.com/users/AndreWohnsland/projects/1) for v2.
The goal of this release is to provide a more polished and at the same time more flexible app.
It includes a new web interface that can be used to control the machine from any device in the same network.
This allows users to control the machine from their phone, tablet, or any other device that has a web browser.
Machines without a display (e.g. Headless) are no longer a dream, you can build and use them now with CocktailBerry.
In addition, the API (backend) is no longer tightly coupled to the frontend.
Advanced users can use the API for their own use, like writing their own frontend or automating tasks over home automation.

## Requirements

It is not recommended to use this on Raspberry Pi 3 series or older, as the performance might not be sufficient.
Use a Raspberry Pi 4 with 2 GB or more of RAM for the best experience.
You need to have an up to date Raspberry Pi OS installed.
The web interface requires a modern web browser that supports the latest web technologies.
You do not need a touch screen, just a device being able to connect to the same network as the Raspberry Pi.
However, a touchscreen can be used to control the app directly on the Raspberry Pi.

As a word of caution: Currently it is difficult to propagate events to open the keyboard on kiosk mode (full screen).
You might start with a none full screen web browser for now, but we are working on a solution.

## Limitations

Currently, the web interface might have some issues with touch screens directly connected to the Raspberry Pi.
In some occasions, older OS or not properly configured screens, the default keyboard might not show up.
If you are using an external device to control the app, this should not be an issue.
In case you are using a touch screen directly connected to the Raspberry Pi, running the browser in non-kiosk mode might help.
Installing maliit keyboard might also be an alternative.

## Installation

The easiest way to use the new interface is to use the CocktailBerry CLI [setup-web command](commands.md#switch-to-cocktailberry-web), once you installed CocktailBerry the usual way.
Existing installations should update to at least version v2.0.0 to have this command available.

!!! warning "Before starting"
    Before you start the update, make sure to backup your data.
    The update should not delete any data, but it is always better to be safe than sorry.
    It is also recommended to have an up to date operating system.
    If you installed CocktailBerry a long time ago, please do a clean install instead of updating.

```bash
cd ~/CocktailBerry
# optional with --ssl to enable https
uv run --python "$(python -V | awk '{print $2}')" --all-extras setup-web
```

This will set up the web interface as the default interface and start it instead of the old main program.
You can now access the the website by opening your browser and navigating to `http://<ip>` or locally on `http://localhost`.
You will need SSL setup if you want to manage backups remotely, see also [setup-web command](commands.md#switch-to-cocktailberry-web).

## Enable the Virtual Keyboard

If you are lucky, the virtual keyboard [squeekboard](https://www.raspberrypi.com/documentation/accessories/display.html#use-an-on-screen-keyboard) is already working out of the box.
In case you do not want it, and it is activated, see the section below to disable it.
If it should not show up when clicking on an input field, you can try to enable it manually.

```bash
cd ~/CocktailBerry
uv run runme.py add-virtual-keyboard
```

## Disable the Virtual Keyboard

If you enabled it via the command above and want to disable it again, you can do so by running the following command.

```bash
cd ~/CocktailBerry
uv run runme.py remove-virtual-keyboard
```

In case you have not enabled it via the command above, you can also disable it by removing over raspi-config.

```bash
sudo raspi-config
```

Then go to `Display Options` -> `On-Screen Keyboard` and disable it.

## Rollback to QT

If you want to go back to the old interface, you can do so by running the following command.

```bash
cd ~/CocktailBerry
uv run switch-back
```
