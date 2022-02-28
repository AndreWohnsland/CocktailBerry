#!/bin/bash
# Setup Script for the CocktailBerry Machine or the Dashboard
# Usage: sh setup.sh [options]
# Options:
# dashboard: set up dashboard, otherwise will set up CocktailBerry

echo "Installing updates, this may take a while..."
sudo apt-get update && sudo apt-get -y upgrade

# Generating launcher script
rm ~/launcher.sh
touch ~/launcher.sh
sudo chmod +x ~/launcher.sh

# using desktop file for autostart
cp ~/CocktailBerry/scripts/cocktail.desktop /etc/xdg/autostart/

cd ~/CocktailBerry/
# Making neccecary steps for the according program
if [ "$1" = "dashboard" ]; then
  echo "Setting up Dashboard"
  echo "cd ~/CocktailBerry/dashboard/frontend" > ~/launcher.sh
  echo "gunicorn --workers=5 --threads=1 -b :8050 index:server" > ~/launcher.sh
  cd dashboard/
  cp frontend/.env.example frontend/.env
  cp qt-app/.env.example qt-app/.env
  docker-compose up --build -d || echo "Could not install backend over docker-compose, is docker installed?"
  cd frontend/
  pip3 install -r requirements.txt
  echo "@chromium-browser --kiosk --app 127.0.0.1:8050" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
else
  echo "Setting up CocktailBerry"
  echo "cd ~/CocktailBerry/" > ~/launcher.sh
  echo "python3 runme.py" > ~/launcher.sh
  pip3 install requests pyyaml GitPython typer pyfiglet
  pip3 install PyQt5 || sudo apt-get -y install qt5-default pyqt5-dev pyqt5-dev-tools || sudo apt-get -y install python3-pyqt5 || echo "Could not install PyQt5"
  cp microservice/.env.example microservice/.env
  echo -n  "Also install microservice (y/n)? This needs docker installed - you can also install it later with docker-compose. "
  read answer
  if echo "$answer" | grep -iq "^y" ;then
      cd microservice/
      docker-compose up --build -d || echo "Could not install microservice over docker-compose, is docker installed?"
  fi
fi
