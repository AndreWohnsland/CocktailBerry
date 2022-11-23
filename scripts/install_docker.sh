#!/bin/bash

echo "Installing Docker"
# Installing Docker
sudo apt-get update && sudo apt-get -y upgrade
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker ${USER}
sudo su - ${USER}
sudo apt-get install docker-compose-plugin
sudo systemctl enable docker