<img src="docs/pictures/CocktailBerry.svg" alt="CocktailBerry"/>

![GitHub release (latest by date)](https://img.shields.io/github/v/release/AndreWohnsland/CocktailBerry)
![GitHub Release Date](https://img.shields.io/github/release-date/AndreWohnsland/CocktailBerry)
![Python Version](https://img.shields.io/badge/python-%3E%3D%203.7-blue)
![GitHub](https://img.shields.io/github/license/AndreWohnsland/CocktailBerry)
![GitHub issues](https://img.shields.io/github/issues-raw/AndreWohnsland/CocktailBerry)
[![Documentation Status](https://readthedocs.org/projects/cocktailberry/badge/?version=latest)](https://cocktailberry.readthedocs.io/en/latest/?badge=latest)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=AndreWohnsland_CocktailBerry&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=AndreWohnsland_CocktailBerry)
![GitHub Repo stars](https://img.shields.io/github/stars/AndreWohnsland/CocktailBerry?style=social)

[![Buy Me a Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow)](https://www.buymeacoffee.com/AndreWohnsland)

CocktailBerry is a Python and Qt based app for a cocktail machine on the Raspberry Pi. Detailed information, installation steps and SetUp can be found at the [Official Documentation](https://cocktailberry.readthedocs.io/).

Supercharge your next party to a whole new level! 🐍 + 🍸 = 🥳 

<div style="display: flex; justify-content: center; align-items: center; margin: 1rem 0rem 1rem 0rem;">
  <a href="https://cocktailberry.readthedocs.io/"
  style="padding: 15px; border-radius: 7px; margin: 0px 10px 0px; text-decoration: none; font-size: x-large; font-weight: bold; color: white !important; background-color: rgb(57, 72, 158);"> 
  Documentation </a>
  <a href="https://share.streamlit.io/andrewohnsland/cocktailberry-webapp"
  style="padding: 15px; border-radius: 7px; margin: 0px 10px 0px; text-decoration: none; font-size: x-large; font-weight: bold; color: white !important; background-color: rgb(255, 40, 102);">
  Dashboard </a>
</div>

This app is used to control a cocktail machine and easily prepare cocktails over a nice-looking user interface. It also offers the option to create and manage your recipes and ingredients over the interface and calculates the possible cocktails to prepare over given ingredients. Track and display cocktail data for different teams to even further increase the fun. Let's get started!

## tl;dr

<img src="docs/pictures/Cocktailmaker_action.gif" alt="Cocktail in the making" width="400"/>

# Features

CocktailBerry can do:

- Prepare cocktails of a given volume and adjusted concentration of alcoholic ingredients
- Add new ingredients and recipes with needed information over the UI
- Specify additional ingredients for later hand add within a recipe (like sticky syrup)
- Define connected ingredients to the machine and also existing additional ingredients over the UI
- Auto calculates and displays possible recipes dependent on given information
- Execute a cleaning program to get rid of remaining fluids
- Export data for later data analysis, send data as mail to a receiver
- Send cocktail production data to a given endpoint, for example a webhook
- Keep track of cocktail count and volume from different teams for some fun competition

In addition, there is the possibility to use and set up a second device as a dashboard:

- Provide the teams API to post and get cocktail data
- Display different modes of data for a by team comparison
- _Optional_: Use the dashboard as WiFi hot-spot


# Quickstart

Here are some simple steps to get CoktailBerry running. You need to have **Python 3.7** or newer and **git** installed.

Run:

```bash
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd CocktailBerry
pip install -r requirements.txt
# you can get help with python runme.py --help
python runme.py
```

This will start the CocktailBerry program. You may want to run the provided installer script for the RPi instead of pip. See [Installation](https://cocktailberry.readthedocs.io/installation/) for more information.

```bash
sh scripts/setup.sh
```

Now you can [Set Up](https://cocktailberry.readthedocs.io/setup/#setting-up-the-machine-modifying-other-values) your CocktailBerry and tweak the settings to your liking.

# Interface

The interface was programmed with PyQt5 for the users to easily interact with CocktailBerry and enter new ingredients/recipes. There are different views for the tasks.

The Maker GUI:

<img src="docs/pictures/Main_ui.png" alt="Maker" width="600"/>

The Ingredient GUI:

<img src="docs/pictures/Ingredients_ui.png" alt="Ingredient" width="600"/>

The Recipe GUI:

<img src="docs/pictures/Recipes_ui.png" alt="Recipe" width="600"/>

The Bottle GUI:

<img src="docs/pictures/Bottles_ui.png" alt="Bottle" width="600"/>

<br/>

# Pull Requests and Issues

If you want to support this project, feel free to fork it and create your own pull request. If you run into any issues, feel free to open a ticket / issue. If you think there is a super important feature missing, open a feature request. It may be implemented in the future.

# Contributing Possibilities

To get started, have a quick look into the [Guidelines for contributing](./CONTRIBUTING.md). Here is a general list of features or refacturing things, I may do in the future. With your help, these things come even faster! If your idea is not on the list, feel free to open a feature request, I may consider it!

- `easy`: Translate all dialogs / UI to your native language
