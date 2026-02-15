#!/bin/bash
# Setup Script for the CocktailBerry Machine or the Dashboard
# Usage: bash setup.sh [options]
# Options:
# dashboard: set up dashboard, otherwise will set up CocktailBerry
# cicd: skip some things for cicd
# v2: set up v2 version

# Parse arguments
V2_FLAG=false
for arg in "$@"; do
  case $arg in
  v2)
    V2_FLAG=true
    shift
    ;;
  *)
    # Assume positional arguments like cicd or dashboard
    break
    ;;
  esac
done

is_raspberry_pi() {
  if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    return 0
  else
    return 1
  fi
}

# check if the model is a Raspberry Pi5
is_raspberry_pi5() {
  if grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    return 0
  else
    return 1
  fi
}

if [[ "$1" = "cicd" ]]; then
  echo "> Skipping update process"
else
  echo "> Updating system, this may take a while..."
  sudo apt update && sudo sudo apt -y full-upgrade
fi

echo "> Installing nmcli, this is needed for wifi setup"
sudo apt install network-manager liblgpio-dev

# using desktop file for autostart
echo "> Copying desktop file to: /etc/xdg/autostart/cocktail.desktop"
sudo cp ~/CocktailBerry/scripts/cocktail.desktop /etc/xdg/autostart/

# also adding the desktop file to the desktop, adding picture to /usr/share/pixmaps
echo "> Copying desktop file to: ~/Desktop/cocktail.desktop"
sudo cp ~/CocktailBerry/scripts/cocktail.desktop ~/Desktop/
sudo chmod +x ~/Desktop/cocktail.desktop
sudo cp ~/CocktailBerry/src/ui_elements/cocktailberry.png /usr/share/pixmaps/cocktailberry.png

# also create an application entry for the start menu
sudo cp ~/CocktailBerry/scripts/cocktail.desktop /usr/share/applications/
sudo chmod +x /usr/share/applications/cocktail.desktop

# Making write permission for all to wpa
# We need this if we want to change wifi settings within CocktailBerry
if [[ -f "/etc/wpa_supplicant/wpa_supplicant.conf" ]]; then
    echo "> Giving write permission to /etc/wpa_supplicant/wpa_supplicant.conf"
    sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf
else
    echo "> Using NetworkManager for WiFi configuration (wpa_supplicant not found)"
fi

if [[ "$1" != "cicd" ]]; then
  cd ~/CocktailBerry/ || exit
fi

# Making necessary steps for the according program
if [[ "$1" = "dashboard" ]]; then
  echo "> Setting up Dashboard"
  cd dashboard/ || exit
  echo -n "Enter your display language (en, de): "
  read -r language
  export UI_LANGUAGE=$language
  docker compose -f docker-compose.both.yaml up --build -d || echo "ERROR: Could not install dashboard over docker-compose, is docker installed?" >&2
  echo "@chromium-browser --kiosk --app 127.0.0.1:8050" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
else
  echo "> Setting up CocktailBerry"
  # Generating launcher script, we use symlinks so when project is updated we can sneak in that change too
  # this might prevent breaking changes on updates
  rm "$HOME/launcher.sh" 2>/dev/null || true
  # script source will be v1-launcher.sh or v2-launcher.sh depending on the flag
  script_source="v1-launcher.sh"
  if [[ "$V2_FLAG" = true ]]; then
    script_source="v2-launcher.sh"
  fi
  echo "> (Re-)Generating launcher script at: ~/launcher.sh, will use $script_source"
  ln -sf "$HOME/CocktailBerry/scripts/$script_source" "$HOME/launcher.sh"
  chmod +x "$HOME/CocktailBerry/scripts/$script_source"

  echo "> Installing needed Python libraries, this may take a while depending on your OS (especially in v1), so it is time for a coffee break :)"
  # v1 needs to sync with system python (for pyqt)
  if [[ "$V2_FLAG" = true ]]; then
    uv sync --inexact --extra nfc || echo "ERROR: Could not install Python libraries with uv" >&2
  else
    echo "> Installing PyQt"
    sudo apt-get -y install python3-pyqt6 || echo "ERROR: Could not install PyQt6" >&2
    uv sync --inexact --extra v1 --extra nfc || echo "ERROR: Could not install Python libraries with uv" >&2
  fi
  if is_raspberry_pi5; then
    sudo usermod -aG gpio "$(whoami)"
    newgrp gpio
    uv pip install lgpio
  fi
  # on none RPi devices, we need to set control to the GPIOs, and set user to sudoers
  if is_raspberry_pi; then
    sudo raspi-config nonint do_i2c 0
  else
    bash scripts/setup_non_rpi.sh
  fi
fi
echo "Done with the setup"
