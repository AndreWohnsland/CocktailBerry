#!/bin/bash

echo "Installing Docker"
sudo apt-get update && sudo apt-get -y upgrade
sudo apt install docker.io -y
docker --version || echo "Docker installation failed :("
echo "Adds current user to docker permissions"
sudo usermod -aG docker $USER
sudo su - $USER
# newgrp docker

# This still seem not to work on rpi
# sudo apt-get install docker-compose-plugin
