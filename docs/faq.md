# Frequently Asked Questions

Here you will find a list of commonly asked questions about the Software or Hardware.
Please make sure to check here first, before asking similar questions.
You may find your solution under the [troubleshooting](troubleshooting.md) section, if it's not here.
Also, there is plenty information at the [setup section](setup.md).


## Hardware

### What are Good Pumps

Any pumps being food save and having a volume flow between 10-50 ml/s are optimal.
Higher or lower values are also possible, but may lead either to longer cocktail preparation time or not perfectly dosed cocktails.
Best pumps to look out for are peristaltic pumps or membrane pumps.
Also take note that currently all pumps run in parallel so check that your power supply is able to power at least 6 pumps at once.

### Which Raspberry Pi is Recommended

My machines still run on the 1GB RAM 3b+ version.
I know of other machines running on a 1/2 GB RAM 4 Version without any problems.
Anything older or with less RAM may work, but is not supported.

### Will CocktailBerry Work Without Internet

Besides pulling this project from GitHub and installing the dependencies at setup, there is no internet connection needed after that.
You will not be able to get auto update notifications without an internet connection or use the microservice to send data to an endpoint.
If the microservice is active and the connection is temporary lost, the data is saved until the internet is back again.

### How to Wire the System

Checkout [this section](hardware.md#possible-basic-circuit), this explains a basic circuit you could use.

### What Display to Use

It depends on how you build your machine, but you will most likely want some sort of touchscreen which can be connected to the Raspberry Pi.
Even an 5-inch 800x480 will work, but in my opinion a 7-inch 1024x600 is quite good.
Higher resolution screen can be used, for high-res screens I recommend [this setting](troubleshooting.md#using-a-high-resolution-screen) for the best user experience.


### Can I use another Board / SBC

You probably can use a wide variety of Single Board Computers (SBCs) beside the Raspberry Pi.
The software should work on any system, but there are still some considerations.
Especially if you are unexperienced with programming and Linux, I strongly suggest to stick to the recommended Pi setup.
If you are experienced with Linux, you can probably get almost any SBC to work properly.
I recommend using a LXDE/XFCE based desktop variant, for example a Debian Linux for the OS.
The autorun / installation may differ a bit from the Pi. 
You also probably need to run the python package installation and program as sudo.
You can switch the board config variable to Generic, this will use the [python-periphery](https://github.com/vsergeev/python-periphery) library.
This library supports a broad variety of SBCs, but the Python process usually needs root permission to access the GPIOs.
In case of any issues related to the GUI (like window positioning, overlap), please take note that officially only the RPi is supported and tested.

## Software

### Which Raspberry Pi OS to Use

Please use the latest Raspberry Pi Desktop OS, currently this is Raspberry Pi OS with desktop in 64 bit, also known as Debian 11 or Bullseye.
These OS run Python 3.9, which is the current mandatory Version of Python to run CocktailBerry.
The 32 bit version should also work fine, just ensure it's the latest Raspberry Pi OS (Debian 11 / Bullseye) as well.
Older OS may work, but are not supported.

### Will Older Python Version Work

Not with the current Version of CocktailBerry.
Best is to use the specified Python version (or newer).
Older version may work, but are not supported.
If you want to run on Python 3.7, use CocktailBerry v1.12 or older.
Please keep in mind that maintenance support of Python 3.7 ends at 2023-06-27.

### How to get Updates

Simply have an internet connection and turn on the check updates option.
If there is an update, CocktailBerry will inform you at startup.

### How to Change Settings

Under the 4th tab (bottles), you will find a gear icon, click on it.
Enter the password (default is 1234 on older versions or none at latest), enter, click on configuration.
There, you will be able to change all possible settings.
See [Setup](setup.md#setting-up-the-machine-modifying-other-values) for a detailed explanation of the configuration options.
The values will also be validated before a change is applies.
The changes may require a restart of the program.

### How to Install CocktailBerry

Check out the [quickstart](quickstart.md) or [installation](installation.md) section.
If you execute those commands at your Raspberry Pi, you should be ready to go.
The commands do: Loading the project from GitHub, updating the system, installing dependencies and creating an auto start setting.

### Can I run Without Pumps

CocktailBerry is a software and therefore will work on any machine, even without any parts of a cocktail machine.
If you want to have a look into the software, you can also install / run it on your PC or Pi.

### Do I Have to Manually Start 

There are different ways to auto start an application on the Raspberry Pi.
The installer script automatically sets up a way, that the program starts after the system is booted.
So after the installation, you just need to turn on your Pi!

### What is the Available Button

If you click the available button under bottles, you get to another window, were you can select ingredients.
On the right side (possible) are all known ingredients, currently not on the left side.
You can put them to the left side (available) or vice versa with the arrow buttons.
Available means, that this ingredient exists / stands besides the maker, but is not connected to a pump.
If a recipe got an ingredient, which should be added via hand / the user later, the machine knows it exists.
So CocktailBerry can accurately offer only recipes where both, machine and hand ingredients are there.

A little tip here: Ingredients connected to the pump are automatically added by the maker.
Ingredients not connected but available will be the ones prompted to be added by hand.
So you can switch from machine to hand or the other way in your setup and CocktailBerry will recognize which is hand and which is machine.

### What is the Password

The default password is 1234 on older versions or none at latest.
A password is at some steps used to prevent unwanted modification of the maker.
Depending on your users, this might be more or less useful but a safety measure.
You can change the password under the settings.

### How many Pumps are Supported

Currently, CocktailBerry supports up to 16 pumps.
This should usually be more than enough and goes well hand in hand with the hardware.
Relays-arrays can have up to 8 switches controlled with one 5V input.
The usual size is 8 (or 16 with an build in converter) relays for a relay board.
In theory, the RPi could control up to 26 pumps when using all possible GPIOs, but that overkill IMHO.

### What is the Inverted Option

Depending on your controlling unit (relay, mosfet, eg.) the on / off signal may be inverted.
The relay arrays I've seen use a high state for switching off and a low state for switching on.
This is the inverted state to a regular n-channel mosfet without any extra elements.
The default setting is set to True, so it's inverted by default and should work as expected with usual relay arrays.

### Do I Need Docker

No, docker is optional.
If you don't understand what docker is or what it does, don't worry.
CocktailBerry will perfectly run without Docker installed.
It's for some optional advanced features you can add anytime you are interested or ready for them.

### How to Exit the Program

If you want to exit the program to get to the desktop, because you want to do some adjustments,
just press alt+F4 in the main program on your keyboard.
Like with most programs, this will exit the current opened program.
You will then be on your desktop.

### I don't Need a Password

Just set the password empty / delete all numbers.
If the password setting ist empty, actions requiring a password will automatically succeed without prompting a password.

### How to Minimize Start Terminal

If you want to minimize the terminal window, you can use xdotool to do so:

```bash
sudo apt-get update
sudo apt-get install xdotool
```
Then adjust the `launcher.sh` file to include the following line on top:

```bash
# you can edit it with 'sudo nano ~/launcher.sh'
sleep 1 # sometimes you need to wait a bit longer so can increase to 2 if needed
xdotool getactivewindow windowminimize
# rest of the script stays same
```

With this setting, the window will be minimized before the rest of the program and output is started.

## Other

### What about Tube Volume

If your pumps got a long tube to the bottle, the first cocktail may have too little volume.
You can set the `MAKER_TUBE_VOLUME` to an approximate value which corresponds to the average of the tube volume.
When applying a new bottle, CocktailBerry will also pump that much volume up.

### Implementing LEDs

You can define one or more pins which control a LED (array).
The LEDs will light up during cocktail preparation, as well when the cocktail is finished.
If it's an controllable WS28x LED you can activate the setting.
Instead of just turning on / off / blinking, the LED will then have some advanced light effects.
If you want to have multiple ring LEDs having the effect synchronously, you can define the number of identical daisy chained rings.
The program will then not treat this chain as one, but as multiple chains.
This does not include some default LEDs used for general lighting of the machine, because they usually don't need controlling.
It's better to directly connect them to the main source current and turn them on when the machine is turned on.

### View Logs

You can either go to the logs folder to have the raw logs.
Or you can go to the option window and select the logs option.
Then you will get a summarized view of the logs.
The latest logs are shown on top. 
Identical logs are only shown once, with their latest occurrence time, as well as count.