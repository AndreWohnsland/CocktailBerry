#!/bin/bash

echo "Installing Docker"
sudo apt-get update && sudo apt-get -y upgrade
sudo apt install docker.io -y
docker --version || echo "Docker installation failed :("
echo "Adds current user to docker permissions"
sudo usermod -aG docker $USER
newgrp docker
echo "Installing Compose"
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-linux-aarch64 -o ~/.docker/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
docker compose version || echo "Compose installation failed :("

# This still seem not to work on rpi
# sudo apt-get install docker-compose-plugin