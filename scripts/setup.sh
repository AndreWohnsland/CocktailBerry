#!/bin/bash
# Setup Script for the CocktailBerry Machine or the Dashboard
# Usage: sh setup.sh [options]
# Options:
# dashboard: set up dashboard, otherwise will set up CocktailBerry

echo "Installing updates, this may take a while..."
sudo apt update && sudo sudo apt -y full-upgrade

# Generating launcher script
echo "(Re-)Generating launcher script at: ~/launcher.sh"
rm ~/launcher.sh
touch ~/launcher.sh
sudo chmod +x ~/launcher.sh

# using desktop file for autostart
echo "Copying desktop file to: /etc/xdg/autostart/cocktail.desktop"
sudo cp ~/CocktailBerry/scripts/cocktail.desktop /etc/xdg/autostart/

# also adding the desktop file to the desktop, addidng picture to /usr/share/pixmaps
echo "Copying desktop file to: ~/Desktop/cocktail.desktop"
sudo cp ~/CocktailBerry/scripts/cocktail.desktop ~/Desktop/
sudo cp ~/CocktailBerry/src/ui_elements/cocktailberry.png /usr/share/pixmaps/cocktailberry.png

# Making write permission for all to wpa
# We need this if we want to change wifi settings within CocktailBerry
echo "Giving write permission to /etc/wpa_supplicant/wpa_supplicant.conf"
sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf

# Since bookworm, venv are not optional but recommended, to not overwrite sys python things
# therefore remove existing and create env for cocktailberry, using system site packages
# This way, pyqt is already there and no pain installing it somehow
echo "(Re-)Creating virtual environment for CocktailBerry, located at ~/.venv-cocktailberry"
rm -rf ~/.env-cocktailberry
python -m venv --system-site-packages ~/.env-cocktailberry
echo "Activating virtual environment, this is needed since Raspbery Pi OS Bookworm"
source ~/.env-cocktailberry/bin/activate

cd ~/CocktailBerry/
# Making neccecary steps for the according program
if [ "$1" = "dashboard" ]; then
  echo "Setting up Dashboard"
  cd dashboard/
  # Letting user choose the frontend type (WebApp or Qt)
  echo -n "Use new dashboard? This is strongly recommended! Oterwise will use old Qt App, but this will only work on a standalone device and has no remote access option (y/n) "
  read answer
  echo -n "Enter your display language (en, de): "
  read language
  # new dashboard
  if echo "$answer" | grep -iq "^y"; then
    export UI_LANGUAGE=$language
    docker compose -f docker-compose.both.yaml up --build -d || echo "ERROR: Could not install dashboard over docker-compose, is docker installed?"
    echo "@chromium-browser --kiosk --app 127.0.0.1:8050" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
  # qt app
  else
    docker compose up --build -d || echo "ERROR: Could not install backend over docker-compose, is docker installed?"
    echo "export UI_LANGUAGE=$language" >>~/launcher.sh
    echo "source ~/.env-cocktailberry/bin/activate" >>~/launcher.sh
    echo "cd ~/CocktailBerry/dashboard/qt-app/" >>~/launcher.sh
    echo "python main.py" >>~/launcher.sh
    cd qt-app/
    pip install -r requirements.txt
  fi
else
  echo "Setting up CocktailBerry"
  echo "source ~/.env-cocktailberry/bin/activate" >>~/launcher.sh
  echo "export QT_SCALE_FACTOR=1" >>~/launcher.sh
  echo "cd ~/CocktailBerry/" >>~/launcher.sh
  echo "python runme.py" >>~/launcher.sh
  echo "Installing PyQt"
  sudo apt-get -y install qt5-default pyqt5-dev pyqt5-dev-tools || sudo apt-get -y install python3-pyqt5 || echo "ERROR: Could not install PyQt5"
  echo "Installing needed Python libraries"
  pip install requests pyyaml GitPython typer pyfiglet qtawesome piicodev mfrc522 pyqtspinner pillow
  # still cp the file, but do not inform the user anymore, since this is not the default anymore
  cp microservice/.env.example microservice/.env
  echo "Install qtsass, this may take a while depending on your OS, so it is time for a coffe break :)"
  echo "If this takes too long for you, you can cancel this step with 'ctrl + c' and install qtsass later manually with 'pip install qtsass'"
  echo "qtsass is needed if you want to customize the CocktailBerry GUI and use your own colors"
  pip install qtsass
fi
echo "Done with the setup"
