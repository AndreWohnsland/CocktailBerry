#!/bin/bash
# Usage: wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash

# Welcome and system updates
echo "~~~~~~~ CocktailBerry All In One Installation Script v1 ~~~~~~~"
echo "Updating system to latest version, depending on your system age, this may take some time ..."
sudo apt-get update && sudo apt-get -y upgrade

# Steps for git
echo "Check if git is installed"
git --version 2>&1 >/dev/null
GIT_IS_AVAILABLE=$?
if [ $GIT_IS_AVAILABLE -ne 0 ]; then
  echo "Git was not found, installing it ..."
  sudo apt install git
else
  echo "Git is already installed!"
fi

# also link python to python3 if its still an old system
echo "linking python to python3 if not already done"
sudo apt install python-is-python3

# steps for python >= 3.9
echo "Check that Python version is at least 3.9"
version=$(python -V 2>&1 | grep -Po '(?<=Python )(.+)')
parsedVersion=$(echo "${version//./}")
echo "Detected version: $version"
if [[ "$parsedVersion" -lt "390" ]]; then
  echo "Python must be at least 3.9. Please upgrade your Python or the system to use CocktailBerry."
  echo "You can check your local Python version with 'python -V'"
  echo "If you have an older system, python3 -V may use the python 3, you should set up python that the python command uses python 3"
  echo "For a tutorial, you can look at https://alluaravind1313.medium.com/make-python3-as-default-in-ubuntu-machine-572431b69094"
  echo "'apt install python-is-python3' may also fix this, but should already be installed previous this step"
  exit 1
else
  echo "You got a valid Python version."
fi

# Warning if debian is not at least v11. Still go on because some users may use none debian
DEBIAN_VERSION=$(sed 's/\..*//' /etc/debian_version)
if [[ "$DEBIAN_VERSION" -lt "11" ]]; then
  echo "WARNING: Your Debian seem not to be at least version 11. It is recommended to update to the latest Raspberry Pi OS!"
fi

# Now gets CocktailBerry source
echo "Getting the CocktailBerry project from GitHub ..."
echo "It will be located at ~/CocktailBerry"
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd ~/CocktailBerry

# Do Docker related steps
echo "Setting things up for Docker and Compose"
bash scripts/install_docker.sh -n
cd ~/CocktailBerry
bash scripts/install_compose.sh

# Now we can finally set the program up ^-^
cd ~/CocktailBerry
echo "Setting up and installing CocktailBerry"
bash scripts/setup.sh

echo "Register successful installation: "
OS_INFO=$(sed -nr 's/^PRETTY_NAME="(.+)"/\1/p' /etc/os-release)
curl -X 'POST' 'https://cocktailberryapi-1-u0613408.deta.app/public/installation' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"os_version": "'"$OS_INFO"'"}'
echo ""

echo "Everything should be set now! Have fun with CocktailBerry :)"
echo "Made by Andre Wohnsland and contributors with <3"
echo "Documentation is found at: https://cocktailberry.readthedocs.io/"
echo "Source code at: https://github.com/AndreWohnsland/CocktailBerry"
echo "If you want to set up your microservice, check the docks for a complete guide. Docker and compose should already be installed."
echo "You can use the CocktailBerry CLI for an interactive setup. Use 'python ~/CocktailBerry/runme.py setup-microservice' to start."
echo "CocktailBerry will start at system start. To start it now, type 'sh ~/launcher.sh'."
echo "If the desctop panel shifts / blocks the application, right click panel > panel settings > Advanced > uncheck Reserve space, and not covered by maximised windows."

newgrp docker
