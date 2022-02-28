#!/bin/bash

echo "Installing Docker"
# Installing Docker
sudo apt-get update && sudo apt-get -y upgrade
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker ${USER}
sudo su - ${USER}
sudo apt-get install libffi-dev libssl-dev
sudo pip3 install docker-compose
sudo systemctl enable docker