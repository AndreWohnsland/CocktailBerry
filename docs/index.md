<img src="./pictures/CocktailBerry.svg" alt="CocktailBerry"/>

![GitHub release (latest by date)](https://img.shields.io/github/v/release/AndreWohnsland/CocktailBerry)
![GitHub Release Date](https://img.shields.io/github/release-date/AndreWohnsland/CocktailBerry)
![Python Version](https://img.shields.io/badge/python-%3E%3D%203.9-blue)
![GitHub](https://img.shields.io/github/license/AndreWohnsland/CocktailBerry)
![GitHub issues](https://img.shields.io/github/issues-raw/AndreWohnsland/CocktailBerry)
[![Documentation Status](https://readthedocs.org/projects/cocktailberry/badge/?version=latest)](https://cocktailberry.readthedocs.io)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=AndreWohnsland_CocktailBerry&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=AndreWohnsland_CocktailBerry)
![GitHub Repo stars](https://img.shields.io/github/stars/AndreWohnsland/CocktailBerry?style=social)

[![Buy Me a Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow)](https://www.buymeacoffee.com/AndreWohnsland)

Welcome to the CocktailBerry documentation.
Here you will find everything to get started!
CocktailBerry is a Python and Qt based app for a cocktail machine on the Raspberry Pi.
It enables you to build your own, fully customized machine, while still be able to use the identical software on each machine.

<div class="mid-flex">
  <a href="quickstart/" class="cta-btn primary-btn"> Quickstart </a>
  <a href="setup/" class="cta-btn secondary-btn"> Set Up </a>
</div>

<!-- <div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __Quick and Easy__

    ---

    Run the provided setup script on your Pi

    [:octicons-arrow-right-24: Quickstart](quickstart.md)

-   :fontawesome-brands-markdown:{ .lg .middle } __Customize to your needs__

    ---

    Change the settings depending on your custom build

    [:fontawesome-solid-gear: Set Up](setup.md)

</div> -->


Supercharge your next party to a whole new level! 🐍 + 🍸 = 🥳 

Like this project? Give it a star on [GitHub](https://github.com/AndreWohnsland/CocktailBerry)! ⭐

## Features

CocktailBerry can do:

- Prepare cocktails of a given volume and adjusted concentration of alcoholic ingredients
- Add new ingredients and recipes with needed information over the UI
- Specify additional ingredients for later hand add within a recipe (like sticky syrup)
- Define connected ingredients to the machine and existing additional ingredients over the UI
- Auto calculates and displays possible recipes dependent on given information
- Supports up to 16 Bottles / Pumps
- Option to serve cocktails without alcohol
- Execute a cleaning program to get rid of remaining fluids
- Export data for later data analysis
- Send cocktail production data to a given endpoint, for example a webhook
- Keep track of cocktail count and volume from different teams for some fun competition
- Select different themes to fit your liking
- Switch between user interface languages
- Support WS281x LEDs on your machine
- Support for RFID/NFC reader
- Implement your own addon to extend the base functionality

In addition, there is the possibility to use and set up a second device as a dashboard:

- Provide the teams API to post and get cocktail data
- Display different modes of data for a by team comparison
- _Optional_: Use the dashboard as WiFi hot-spot