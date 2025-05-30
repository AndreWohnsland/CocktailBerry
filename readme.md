<img src="docs/pictures/CocktailBerry.svg" alt="CocktailBerry"/>

![GitHub release (latest by date)](https://img.shields.io/github/v/release/AndreWohnsland/CocktailBerry)
![GitHub Release Date](https://img.shields.io/github/release-date/AndreWohnsland/CocktailBerry)
![Python Version](https://img.shields.io/badge/python-%3E%3D%203.11-blue)
![GitHub](https://img.shields.io/github/license/AndreWohnsland/CocktailBerry)
![GitHub issues](https://img.shields.io/github/issues-raw/AndreWohnsland/CocktailBerry)
[![Documentation Status](https://readthedocs.org/projects/cocktailberry/badge/?version=latest)](https://cocktailberry.readthedocs.io)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=AndreWohnsland_CocktailBerry&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=AndreWohnsland_CocktailBerry)
![GitHub Repo stars](https://img.shields.io/github/stars/AndreWohnsland/CocktailBerry?style=social)

[![Support CocktailBerry](https://img.shields.io/badge/Support%20CocktailBerry-donate-yellow)](https://www.buymeacoffee.com/AndreWohnsland)

CocktailBerry is a Python and Qt (or React for v2) based app for a cocktail machine on the Raspberry Pi.
It enables you to build your own, fully customized machine, while still be able to use the identical software on each machine.
Detailed information, installation steps and SetUp can be found at the [Official Documentation](https://docs.cocktailberry.org).

<a href="https://demo.cocktailberry.org/"><img src="docs/pictures/demobutton.png" alt="v2-demo" height="70"/></a>

Supercharge your next party to a whole new level! 🐍 + 🍸 = 🥳

<a href="https://cocktailberry.org/"><img src="docs/pictures/websitebutton.png" alt="website" height="70"/></a>
<a href="https://docs.cocktailberry.org/"><img src="docs/pictures/docbutton.png" alt="documentation" height="70"/></a>
<a href="https://stats-cocktailberry.streamlit.app/"><img src="docs/pictures/dashboardbutton.png" alt="dashboard" height="70"/></a>

This app is used to control a cocktail machine and easily prepare cocktails over a nice-looking user interface.
It also offers the option to create and manage your recipes and ingredients over the interface and calculates the possible cocktails to prepare over given ingredients.
Track and display cocktail data for different teams to even further increase the fun.
Let's get started!

Like this project? Give it a star on GitHub! ⭐

## tl;dr

<img src="docs/pictures/Cocktailmaker_action.gif" alt="Cocktail in the making" width="400"/>

# Features

CocktailBerry currently comes in two versions, v1 and v2.
The v1 is the stable version which ships the QT app as a single application.
[v2](https://docs.cocktailberry.org/web/) is the new version with a separate API and UI, which offers more flexibility, but might have some issues on build in touchscreens.
Both versions have the full feature set listed below.

CocktailBerry can do:

- Prepare cocktails of a given volume and adjusted concentration of alcoholic ingredients
- Add new ingredients and recipes with needed information over the UI
- Specify additional ingredients for later hand add within a recipe (like sticky syrup)
- Define connected ingredients to the machine and existing additional ingredients over the UI
- Auto calculates and displays possible recipes dependent on given information
- Option to serve cocktails without alcohol
- Execute a cleaning program to get rid of remaining fluids
- Visualize the cocktail data and get insights
- Run headless, so you can access it over another device
- Send cocktail production data to a given endpoint, for example a webhook
- Keep track of cocktail count and volume from different teams for some fun competition
- Select different themes to fit your liking
- Switch between user interface languages
- Support WS281x LEDs on your machine
- Support for RFID/NFC reader
- Implement your own [addon](https://github.com/AndreWohnsland/CocktailBerry-Addons) to extend the base functionality

In addition, there is the possibility to use and set up a second device as a dashboard:

- Provide the teams API to post and get cocktail data
- Display different modes of data for a by team comparison
- _Optional_: Use the dashboard as WiFi hot-spot

# Quickstart

Here are some simple steps to get CocktailBerry running. You need to have **Python 3.11** or newer and **git** installed.

On the RPi, you can try the new [all in one installer script](https://github.com/AndreWohnsland/CocktailBerry/blob/master/scripts/all_in_one.sh).
One command should install everything:

```bash
wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash
```

Otherwise, you can manually install it using [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd CocktailBerry
uv venv --system-site-packages
uv sync --all-extras
uv run runme.py
```

This will start the CocktailBerry program. You may want to run the provided installer script for the RPi instead of pip.
See [Installation](https://cocktailberry.readthedocs.io/installation/) for more information.

```bash
sh scripts/setup.sh
```

Now you can [Set Up](https://cocktailberry.readthedocs.io/setup/#setting-up-the-machine-modifying-other-values) your CocktailBerry and tweak the settings to your liking.

# Interface

The interface was programmed with PyQt5 for the users to easily interact with CocktailBerry and enter new ingredients/recipes.
There are different views for the tasks.

The Maker GUI:

<img src="docs/pictures/Main_ui.png" alt="Maker" width="600"/>

<img src="docs/pictures/Selection_ui.png" alt="Maker" width="600"/>

The Ingredient GUI:

<img src="docs/pictures/Ingredients_ui.png" alt="Ingredient" width="600"/>

The Recipe GUI:

<img src="docs/pictures/Recipes_ui.png" alt="Recipe" width="600"/>

The Bottle GUI:

<img src="docs/pictures/Bottles_ui.png" alt="Bottle" width="600"/>

<br/>

# Pull Requests and Issues

If you want to support this project, feel free to fork it and create your own pull request.
If you run into any issues, feel free to open a ticket / issue.
If you think there is a super important feature missing, open a feature request.
It may be implemented in the future.

# Contributing Possibilities

To get started, have a quick look into the [Guidelines for contributing](./CONTRIBUTING.md).
Here is a general list of features or refactoring things, I may do in the future.
With your help, these things come even faster!
If your idea is not on the list, feel free to open a feature request, I may consider it!

- `easy`: Translate all dialogs / UI to your native language
- `easy-hard`: Implement a cool [addon](https://github.com/AndreWohnsland/CocktailBerry-Addons) and make it verified

# Development

This project uses [uv](https://docs.astral.sh/uv/) to manage all its dependencies.
To get started, you need to install uv and then install the dependencies.
See also at the [dev notes](./docs/.devnotes.md) section for a complete run down as well as extra information.

```bash
uv sync --all-extras
```

We also use pre-commits to check the code style and run some tests before every commit.
You can install them with:

```bash
uv run pre-commit install --install-hooks
```

This will install all dependencies and you can start developing.
Then just run:

```bash
uv run runme.py
```

If you want to develop the api, you can also run it with

```bash
uv run fastapi dev ./src/api/api.py
```
