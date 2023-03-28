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
fi

# steps for python >= 3.9
echo "Check that Python version is at least 3.9"
version=$(python -V 2>&1 | grep -Po '(?<=Python )(.+)')
parsedVersion=$(echo "${version//./}")
if [[ "$parsedVersion" -lt "390" ]]; then
  echo "Python must be at least 3.9. Please upgrade your Python or the system to use CocktailBerry."
  exit 1
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
sh scripts/install_docker.sh
cd ~/CocktailBerry
sh scripts/install_compose.sh

# Now we can finally set the program up ^-^
cd ~/CocktailBerry
echo "Setting up and installing CocktailBerry"
sh scripts/setup.sh

echo "Everything should be set now! Have fun with CocktailBerry :)"
echo "Made by Andre Wohnsland and contributors with <3"
echo "Documentation is found at: https://cocktailberry.readthedocs.io/"
echo "Source code at: https://github.com/AndreWohnsland/CocktailBerry"