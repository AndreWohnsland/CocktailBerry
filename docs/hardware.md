# Hardware

You can also run the interface on any non RPi hardware, but you won't be able to control the pins without a device supporting this.
To build a functional machine, I provided a list of my used hardware.
This is merely a suggestion.
How exactly you will build your CocktailBerry is completely up to you.

## Showcase Machine

The following components were used within the showcase for the Machine:

- 1x [Raspberry Pi 3b+](http://www.amazon.de/dp/B00LPESRUK/) (or newer like [Model 4](https://www.amazon.de/gp/product/B07TD42S27))
- 1x [5-inch Touch Screen](http://www.amazon.de/dp/B071XT9Z7H/) for the Raspberry Pi
- 1x Micro SD-Card (16 Gb is enough)
- 1x 5V Power supply for the Raspberry Pi
- 1x or 2x [Relay-Boards](https://www.amazon.de/gp/product/B07MJF9Z4K) depending on pump count (important to have 5V input control)
- 6-10x Pumps, depending on your setup (you can use a [peristaltic pump](https://www.amazon.de/gp/product/B07YWGSH3C/) or a [membrane pump](http://www.amazon.de/dp/B07L1FB18S/), it should be food save)
- 1x Power supply for the pumps (a 12V/5A Laptop charger in my case, needs to match pump voltage)
- Food safe hose/tubes for the pumps
- Female to Female jumper wires
- Female to Male HDMI and USB extension cable
- Some wires

## Showcase Teams Dashboard

The following components were used within the showcase for the Teams Dashboard:

- 1x [Raspberry Pi 3b+](http://www.amazon.de/dp/B00LPESRUK/) (or newer, like [Model 4](https://www.amazon.de/gp/product/B07TD42S27))
- 1x [7-inch Touch Screen](http://www.amazon.de/dp/B014WKCFR4/)
- 1x [Display Casing](http://www.amazon.de/dp/B01GQFUWIC/)
- 1x Micro SD-Card (16 Gb is enough)
- 1x 5V Power supply for the Raspberry Pi

## Possible Basic Circuit

The following picture shows a possible circuit for CocktailBerry.
The Raspberry Pi will provide too litte power / current to operate the pumps.
You have to use two power circuits, one for powering the Raspberry Pi and one for the pumps.
The pump circuit will be most likely 12 or 24 V.
You can either use two different power supplies or use a step down converter for the RPi.
The RPi will control a relay, mosfet or another electrical switch over the GPIO output.

<img src="../pictures/circuit.jpg" alt="circuit"/>

You can use any of the GPIOs of the RPi, the connected pump to that pin can be defined in the config.
The switch will then turn the pump on or of over the RPi.
How you will build your CocktailBerry is still completely up to you.
The only restriction by the software is that the GPIO pins are turned on / off over the RPi.

## Custom PCBs or STLs

I am currently working on a custom PCB for even easier connection and cable management.
This topic is quite new to me, so if you are interested in helping [reach out to me](mailto:cocktailmakeraw@gmail.com).
With your help, we can make this project even better.

When the PCB is in an acceptable state, I will also work on a new design fitting for that PCB.
Somewhen in the future, you may find the according files here at this place, or a link to its origin.