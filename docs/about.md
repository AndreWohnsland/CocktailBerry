# Overview

CocktailBerry is used to control a cocktail your machine and easily prepare cocktails over a nice-looking user interface.
It also offers the option to create and manage your recipes and ingredients over the interface and calculates the possible cocktails to prepare over given ingredients.
Track and display cocktail data for different teams to even further increase the fun.
Have also a look into the [User Guide](assets/CocktailBerryUserGuide.pdf).
Let's get started!

## tl;dr

You can easily install the software by just flashing the Raspberry Pi OS on a SD card, insert it, start the device and install the software with just one command.
Then, get some coffee and let the script do the work.
When you come back, you can set up the machine over the graphical user interface and start mixing cocktails.
This way, you don't have to know much about software an can go full focus on the hardware.
If you want to do your own software part, you can still add this over [addons](addons.md).

<figure markdown>
  ![Cocktail in the making](pictures/Cocktailmaker_action.gif){ width="600" }
  <figcaption>User selects recipe > clicks button > cocktail is prepared > profit</figcaption>
</figure>

## Interface

CocktailBerry comes with two versions: v1 and v2.
Most impressions here shown are from v1, but v2 is quite similar.
The main difference is that v2 comes with a more modern design and as a web app, offering more flexibility and accessibility.
You can have a look at the [v2 demo](https://demo.cocktailberry.org/cocktails) to interactively experience it.
The interface was programmed for the users to easily interact with CocktailBerry and manage everything over the GUI.
There are different views for the tasks.

<figure markdown>
  ![Maker](pictures/Main_ui.png)
  <figcaption>The Maker GUI</figcaption>
</figure>

<figure markdown>
  ![Selection](pictures/Selection_ui.png)
  <figcaption>The Selection GUI</figcaption>
</figure>

This is the main window of the application and the window your guest will interact with.
They can choose a cocktail of their choice, a crossed glass at the start indicates that there is also a virgin option of this cocktail.
The cocktail data is displayed after selection.
The user can choose from your defined list of volume, as well as the alcohol level of the cocktail.

<figure markdown>
  ![Ingredient](pictures/Ingredients_ui.png)
  <figcaption>The Ingredient GUI</figcaption>
</figure>

Here you can manage all your ingredients.
Define the name, volume and alcohol level of each ingredient here.
Also, you can set ingredients for hand add and define a custom unit for the handadd.
This is extremely handy, if you want to prompt the user to add a slice of something at the end.

<figure markdown>
  ![Recipe](pictures/Recipes_ui.png)
  <figcaption>The Recipe GUI</figcaption>
</figure>

Here you can manage all your recipes.
Define the name and ingredients with corresponding volume.
You can disable recipes, you currently don't want to serve, or activates the virgin option for a cocktail.
The number after the ingredient defines the order of the ingredients in the cocktail, same numbers are added in parallel.

<figure markdown>
  ![Bottle](pictures/Bottles_ui.png)
  <figcaption>The Bottle GUI</figcaption>
</figure>

Here you can manage your connected ingredients.
Toggle the new button and apply a new ingredient if you change to a new bottle.
You can also change the current fill level of each bottle.
Use the gear icon to get to the option window.
Within this, you can export data, change settings, make and restore backups or reboot and shutdown the system.

## Example Machines

The base machine consists out of a Raspberry Pi + touchscreen, 5V relays as well as membrane pumps and some cabling.
Using wood, metal or 3D printed parts for the housing, you can create a very nice-looking cocktail machine.
There are a lot of custom-builds out there, check out the [official dashboard](https://stats-cocktailberry.streamlit.app/#existing-machines) for more impressions.
See [Hardware](hardware.md) for a detailed example list of components.
You can also have a look at the official website for cocktailberry for more examples and information: [cocktailberry.org](https://cocktailberry.org).
