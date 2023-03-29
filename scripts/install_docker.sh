#!/bin/bash

# If the -n flag is there, will not do reload
# This is mainly used for the all in one script.
RELOAD_GRP='true'
while getopts ':n' 'OPTKEY'; do
  case ${OPTKEY} in
  'n')
    RELOAD_GRP='false'
    ;;
  '?')
    echo "INVALID OPTION -- ${OPTARG}" >&2
    exit 1
    ;;
  ':')
    echo "MISSING ARGUMENT for option -- ${OPTARG}" >&2
    exit 1
    ;;
  *)
    echo "UNIMPLEMENTED OPTION -- ${OPTKEY}" >&2
    exit 1
    ;;
  esac
done

echo "Installing Docker"
sudo apt-get update && sudo apt-get -y upgrade
sudo apt install docker.io -y
docker --version || echo "Docker installation failed :("
echo "Adds current user to docker permissions"
sudo usermod -aG docker $USER

if ${RELOAD_GRP}; then
  newgrp docker
fi

# This still seem not to work on rpi
# sudo apt-get install docker-compose-plugin
