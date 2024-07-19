#!/bin/bash

# Check if the script is running on a non-Raspberry Pi device
if ! is_raspberry_pi; then
  echo "$(whoami) ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/99_$(whoami)_nopasswd >/dev/null
  sudo chmod 0440 /etc/sudoers.d/99_$(whoami)_nopasswd
  if ! getent group gpio >/dev/null; then
    echo "Creating gpio group"
    sudo groupadd gpio
  fi
  echo "Setting up GPIOs for non Raspberry Pi devices"
  sudo usermod -aG gpio $USER

  # Create the setup_gpio_permissions.sh script
  sudo cp .scripts/setup_gpio_permissions.sh /usr/local/bin/setup_gpio_permissions.sh
  sudo cp .scripts/setup_gpio_permissions.service /etc/systemd/system/setup_gpio_permissions.service

  # Make the script executable
  sudo chmod +x /usr/local/bin/setup_gpio_permissions.sh
  sudo systemctl enable setup_gpio_permissions.service
  sudo systemctl start setup_gpio_permissions.service

  # Execute the script to apply permissions immediately
  sudo /usr/local/bin/setup_gpio_permissions.sh

  # set the rules to enable gpio
  # only both in combination seem to work
  sudo apt install python3-pip libgpiod2
  sudo cp .scripts/99-gpio.rules /etc/udev/rules.d/99-gpio.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger

  echo "Please reboot your device now, to apply the changes"
fi
