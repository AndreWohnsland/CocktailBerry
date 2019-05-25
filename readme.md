# Cocktailmaker by Andre Wohnsland

Hello everyone, I am *Andre Wohnsland*, a German Master Engineer in Renewable Energy Systems, trying to get better in Python every day.\
This is my first published project, a RaspberryPi app for a custom designed Cocktailmaker also created by me.\
I am also planning to do a showcase of the whole machine (it's already running well) but currently i haven't had the time.\
This app is currently under further construction and adding new functionalities, as well as optimising the code (readability and efficiency).\
It also serves to get more used to version control, since it's also my first time using it.\
If you got any questions or proposed improvements, feel free to share and/or contact me.

## Minimal Requirements

Python 3\
PyQt5\
RaspberryPi 3

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

As long as you are working on another hardware (for example on a Windows or macOS engine) there aren't some Pi-specific imports.\
Therefore you need to set:
```
devenvironment = True
```

## Adding new Recipes or Ingredients

At the moment, there are only limited ingredients and recipes. But you can add your own to the program as well.\
This app uses a sqlite3 DB coupled to the UI. So it's quite easy to implement new ingredients or even recipes.\
Just use the implemented UI for the procedure under the according tabs (**Zutaten** or **Rezepte**).\
To enable/disable the recipe tab set:
```
partymode = False
or
partymode = True
```
accordingly.
All entered Values are checked for reason and if something is wrong, an error message will inform the user what's wrong with the data input.\
If you want to browse through the DB I recommend some program like [DB Browser for sqlite](https://sqlitebrowser.org/).

## Modifying other Values (Pins, Volume Flow, Password)

These values are stored under the `globals.py` file and can be changed. `usedpins` are the RPi-Pins where each Pump is connected and `pumpvolume` the according volume flow in ml/s.\
Depending on your Pumps and connection of the Pi, these can differ from mine.

## Setting up the Machine

Setting up the machine is quite easy as well. Just go to the ***Belegung*** Tab and select via the dropdow boxes your assigned ingredients.\
The program will then evaluate which recipe meets all requirements (e.g. all ingredients are available) and the recipe will be shown in the ***Maker*** Tab.

## Problems while Running the Program

All cases (e.g. not enough of one ingredient, no/wrong values ...) should be handled and a info message should be displayed.\
If in any case any unexpected behaviour occurs feel free to contact me. 