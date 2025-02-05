#!/bin/bash
# Setup Script for the CocktailBerry Machine or the Dashboard
# Usage: bash setup.sh [options]
# Options:
# dashboard: set up dashboard, otherwise will set up CocktailBerry

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

echo "> Installing updates, this may take a while..."
sudo apt update && sudo sudo apt -y full-upgrade

echo "> Installing nmcli, this is needed for wifi setup"
sudo apt install network-manager

# Generating launcher script
echo "> (Re-)Generating launcher script at: ~/launcher.sh"
rm ~/launcher.sh
touch ~/launcher.sh
sudo chmod +x ~/launcher.sh

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
echo "> Giving write permission to /etc/wpa_supplicant/wpa_supplicant.conf"
sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf

cd ~/CocktailBerry/ || exit
# creating project venv with uv
echo "> Creating project venv with uv"
uv venv --system-site-packages --python "$(python -V | awk '{print $2}')" || echo "ERROR: Could not create venv with uv, is uv installed?"

# Making necessary steps for the according program
if [ "$1" = "dashboard" ]; then
  echo "> Setting up Dashboard"
  cd dashboard/ || exit
  # Letting user choose the frontend type (WebApp or Qt)
  echo -n "Use new dashboard? This is strongly recommended! Otherwise will use old Qt App, but this will only work on a standalone device and has no remote access option (y/n) "
  read -r answer
  echo -n "Enter your display language (en, de): "
  read -r language
  # new dashboard
  if echo "$answer" | grep -iq "^y"; then
    export UI_LANGUAGE=$language
    docker compose -f docker-compose.both.yaml up --build -d || echo "ERROR: Could not install dashboard over docker-compose, is docker installed?"
    echo "@chromium-browser --kiosk --app 127.0.0.1:8050" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
  # qt app
  else
    docker compose up --build -d || echo "ERROR: Could not install backend over docker-compose, is docker installed?"
    {
      echo "export UI_LANGUAGE=$language"
      echo "source ~/CocktailBerry/.venv/bin/activate"
      echo "cd ~/CocktailBerry/dashboard/qt-app/"
      echo "python main.py"
    } >>~/launcher.sh
    cd qt-app/ || exit
    pip install -r requirements.txt
  fi
else
  echo "> Setting up CocktailBerry"
  {
    echo "export QT_SCALE_FACTOR=1"
    echo "cd ~/CocktailBerry/"
    echo "uv venv --system-site-packages --python \"$(python -V | awk '{print $2}')\""
    echo "uv run --python \"$(python -V | awk '{print $2}')\" --all-extras runme.py"
  } >>~/launcher.sh
  echo "> Installing PyQt"
  sudo apt-get -y install qt5-default pyqt5-dev pyqt5-dev-tools || sudo apt-get -y install python3-pyqt5 || echo "ERROR: Could not install PyQt5"
  echo "> Installing needed Python libraries, including qtsass, this may take a while depending on your OS, so it is time for a coffee break :)"
  uv sync --all-extras
  if is_raspberry_pi5; then
    sudo usermod -aG gpio "$(whoami)"
    newgrp gpio
  fi
  # on none RPi devices, we need to set control to the GPIOs, and set user to sudoers
  if ! is_raspberry_pi; then
    ./setup_non_rpi.sh
  fi
  # still cp the file, but do not inform the user anymore, since this is not the default anymore
  cp microservice/.env.example microservice/.env
fi
echo "Done with the setup"
