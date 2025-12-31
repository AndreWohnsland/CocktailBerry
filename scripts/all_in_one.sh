#!/bin/bash
# Usage: wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash [-s v2]

# Parse arguments
V2_FLAG=false
DEV_FLAG=false
for arg in "$@"; do
  case $arg in
  v2)
    V2_FLAG=true
    shift
    ;;
  dev)
    DEV_FLAG=true
    shift
    ;;
  *)
    echo "Invalid option: $arg" 1>&2
    exit 1
    ;;
  esac
done

# Welcome and system updates
echo "~~~~~~~ CocktailBerry All In One Installation Script ~~~~~~~~"
echo "> Source taken from: https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh"
if [[ "$V2_FLAG" = true ]]; then
  echo "> You are installing the v2 (Web) version of CocktailBerry"
else
  echo "> You are installing the v1 (Qt) version of CocktailBerry"
fi
echo "~~ Updating system to latest version, depending on your system age, this may take some time ... ~~"
sudo apt-get update && sudo apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade

# Steps for git
echo "~~ Check if git is installed ~~"
git --version >/dev/null 2>&1
GIT_IS_AVAILABLE=$?
if [[ $GIT_IS_AVAILABLE -ne 0 ]]; then
  echo "> Git was not found, installing it ..."
  sudo apt install git
else
  echo "> Git is already installed!"
fi

# also link python to python3 if its still an old system
echo "~~ linking python to python3 if not already done ~~"
sudo apt install python-is-python3

# steps for python >= 3.11
echo "~~ Check that Python version is at least 3.11 ~~"
version=$(python -V 2>&1 | grep -Po '(?<=Python )(.+)')
parsedVersion="${version//./}"
echo "> Detected version: $version"
if [[ "$parsedVersion" -lt "3110" ]]; then
  echo "> Python must be at least 3.11. Please upgrade your Python or the system to use CocktailBerry."
  echo "> You can check your local Python version with 'python -V'"
  echo "> If you have an older system, python3 -V may use the python 3, you should set up python that the python command uses python 3"
  echo "> For a tutorial, you can look at https://alluaravind1313.medium.com/make-python3-as-default-in-ubuntu-machine-572431b69094"
  echo "> 'apt install python-is-python3' may also fix this, but should already be installed previous this step"
  exit 1
else
  echo "> You got a valid Python version."
fi

# might also need to install python-venv
echo "~~ Check if python3-venv and ensurepip are available ~~"
python3 -m venv --help >/dev/null 2>&1
VENV_IS_AVAILABLE=$?
python3 -c "import ensurepip" >/dev/null 2>&1
ENSUREPIP_IS_AVAILABLE=$?

if [[ $VENV_IS_AVAILABLE -ne 0 ]] || [[ $ENSUREPIP_IS_AVAILABLE -ne 0 ]]; then
  echo "> Python3 venv or ensurepip was not found, installing python3-venv ..."
  PYTHON_VERSION=$(python3 -V | cut -d' ' -f2 | cut -d'.' -f1,2) # Extracts version in format X.Y
  sudo apt install python"${PYTHON_VERSION}"-venv
else
  echo "> Python3 venv and ensurepip are already installed!"
fi

# also install pip if not already done
echo "~~ Check if pip is installed ~~"
pip --version >/dev/null 2>&1
PIP_IS_AVAILABLE=$?
if [[ $PIP_IS_AVAILABLE -ne 0 ]]; then
  echo "> Pip was not found, installing it ..."
  sudo apt install python3-pip
else
  echo "> Pip is already installed!"
fi

echo "~~ Installing uv ~~"
curl -LsSf https://astral.sh/uv/install.sh | sh
# shellcheck disable=SC1091
source "$HOME"/.local/bin/env

# Warning if debian is not at least v12. Still go on because some users may use none debian
# Check if /etc/debian_version exists
if [ -f /etc/debian_version ]; then
  # Extract the major version number of Debian
  DEBIAN_VERSION=$(sed 's/\..*//' /etc/debian_version)
  if [[ "$DEBIAN_VERSION" -lt "12" ]]; then
    echo "WARNING: Your Debian seems not to be at least version 12. It is recommended to update to the latest Raspberry Pi OS!"
  fi
else
  echo "WARNING: /etc/debian_version not found. This script might not work properly on none debian systems."
fi

# ensure lxterminal is installed
echo "~~ Check if lxterminal is installed ~~"
lxterminal --version >/dev/null 2>&1
LXTERMINAL_IS_AVAILABLE=$?
if [[ $LXTERMINAL_IS_AVAILABLE -ne 0 ]]; then
  echo "> Lxterminal was not found, installing it ..."
  sudo apt install lxterminal
else
  echo "> Lxterminal is already installed!"
fi

# Now gets CocktailBerry source
echo "~~ Getting the CocktailBerry project from GitHub ... ~~"
echo "> It will be located at ~/CocktailBerry"
# shellcheck disable=SC2164
cd ~
# if folder exist, backup the "custom_config.yaml" and "Cocktail_database.db" if they exist
if [[ -d ~/CocktailBerry ]]; then
  # create cocktailberry backup folder if not exists
  echo "> CocktailBerry folder already exists. Backing up existing important files ..."
  mkdir -p ~/cocktailberry_backups
  timestamp=$(date +"%Y%m%d_%H%M%S")
  target_backup_folder=~/cocktailberry_backups/"$timestamp"
  echo "> Creating backup folder at: $target_backup_folder"
  mkdir -p "$target_backup_folder"
  for file in Cocktail_database.db custom_config.yaml; do
    src=~/CocktailBerry/"$file"
    if [[ -e "$src" ]]; then
      cp -p "$src" "$target_backup_folder/$file"
    fi
  done
  echo "> Removing old CocktailBerry ..."
  sudo rm -rf ~/CocktailBerry
fi

git clone https://github.com/AndreWohnsland/CocktailBerry.git
# shellcheck disable=SC2164
cd ~/CocktailBerry
# if in dev mode, checkout the dev branch
if [[ "$DEV_FLAG" = true ]]; then
  echo "~~ [INFO] DEV flag is set, checking out the dev branch ~~"
  git checkout dev
fi

# Do Docker related steps
echo "~~ Setting things up for Docker and Compose ~~"
bash scripts/install_docker.sh -n
# shellcheck disable=SC2164
cd ~/CocktailBerry
bash scripts/install_compose.sh

# Need to set up NFC reader before installing the python nfc libraries
# shellcheck disable=SC2164
cd ~/CocktailBerry
echo "~~ Setting up NFC USB Reader configuration ~~"
bash scripts/setup_usb_nfc.sh || true

# Now we can finally set the program up ^-^
# shellcheck disable=SC2164
cd ~/CocktailBerry
echo "~~ Setting up and installing CocktailBerry ~~"
if [[ "$V2_FLAG" = true ]]; then
  bash scripts/setup.sh v2
else
  bash scripts/setup.sh
fi

echo "~~ Register successful installation: ~~"
OS_INFO=$(sed -nr 's/^PRETTY_NAME="(.+)"/\1/p' /etc/os-release)
if [[ -z "$OS_INFO" ]]; then
  OS_INFO="not provided"
fi
curl -X 'POST' 'https://api.cocktailberry.org/api/v1/public/installation' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"os_version": "'"$OS_INFO"'"}'
echo ""

if [[ "$V2_FLAG" = true ]]; then
  echo "~~ Finalizing Web Setup ~~"
  # shellcheck disable=SC2164
  cd ~/CocktailBerry
  uv run api.py setup-web
  # informs the user that with v2 he still needs to run cocktailberry before opening the web
  echo "> !!! You need to run 'bash ~/launcher.sh' or click the CocktailBerry icon before opening the web interface."
  echo "> !!! When CocktailBerry is running, you can open the web interface at http://localhost in the web or over the CocktailBerry Web icon."
fi

echo "~~ Everything should be set now! Have fun with CocktailBerry :) ~~"
echo "> Made by Andre Wohnsland and contributors with <3"
echo "> Documentation is found at: https://docs.cocktailberry.org/"
echo "> Source code at: https://github.com/AndreWohnsland/CocktailBerry"
echo "> If you want to set up your microservice, check the docks for a complete guide. Docker and compose should already be installed."
echo "> You can use the CocktailBerry CLI for an interactive setup. Use 'python ~/CocktailBerry/runme.py setup-microservice' to start."
echo "> CocktailBerry will start at system start. To start it now, type 'bash ~/launcher.sh' or click the CocktailBerry icon."
echo "> If the desktop panel shifts / blocks the application, right click panel > panel settings > Advanced > uncheck Reserve space, and not covered by maximised windows."
echo "> Please close this terminal and open a new one to start using CocktailBerry."
newgrp docker
