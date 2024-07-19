#!/bin/bash
sudo chown -R root:gpio /sys/class/gpio
sudo chmod -R ug+rw /sys/class/gpio
sudo chown root:gpio /sys/class/gpio/export /sys/class/gpio/unexport
sudo chmod ug+rw /sys/class/gpio/export /sys/class/gpio/unexport
