# Frequently Asked Questions

Here you will find a list of commonly asked questions about the Software or Hardware.
Please make sure to check here first, before asking similar questions.
Also, you may find your solution under the [troubleshooting](troubleshooting.md) section, if it's not here.

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

## Software

### Which Raspberry Pi OS to Use

Please use the latest 64 bit Raspberry Pi Desktop OS, currently this is Raspberry Pi OS with desktop in 64 bit.
These OS run Python 3.9, which is the current mandatory Version.
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
Enter the password (default is 1234), enter, click on change settings.
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

### Do I Need Docker

No, docker is optional.
If you don't understand what docker is or what it does, don't worry.
CocktailBerry will perfectly run without Docker installed.
It's for some optional advanced features you can add anytime you are interested or ready for them.

## Other

### What about Tube Volume

If your pumps got a long tube to the bottle, the first cocktail may have too little volume.
You can set the `MAKER_TUBE_VOLUME` to an approximate value which corresponds to the average of the tube volume.
When applying a new bottle, CocktailBerry will also pump that much volume up.