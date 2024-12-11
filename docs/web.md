# CocktailBerry Web

This is within the [roadmap](https://github.com/users/AndreWohnsland/projects/1) for v2.
The goal of this release is to provide a more polished and at the same time more flexible app.
It includes a new web interface that can be used to control the app from any device in the same network.
This allows users to control the app from their phone, tablet, or any other device that has a web browser.
Machines without a display (e.g. Headless) are no dream any longer, you can build and use them now with CocktailBerry.
In addition, the api (backend) is no longer tightly coupled to the frontend.
Advanced users can use the API for their own use, like writing their own frontend or automating tasks over home automation.

!!! info "This is in Beta State"
    This is a fairly new implementation and still in Beta state.
    If you spot any issues, please report them in the [GitHub repository](https://github.com/AndreWohnsland/CocktailBerry/issues/new/choose).
    In general, most features should work as expected, but there might be some edge cases that are not covered yet.

## Installation

The easiest way to use the new interface is to use the cocktailberry cli, once you installed CocktailBerry the usual way.
Existing installations should update to at least version v2.0.0 to have this command available.

```bash
cd ~/CocktailBerry
# active virtual environment at newer installations
source ~/.env-cocktailberry/bin/activate
python runme.py setup-web
```

This will set up the web interface as the default interface and start it instead of the old main program.

## Rollback

If you want to go back to the old interface, you can do so by running the following command.

```bash
cd ~/CocktailBerry
# active virtual environment at newer installations
source ~/.env-cocktailberry/bin/activate
python runme.py switch-back
```
