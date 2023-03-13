#!/bin/bash

echo "Installing Compose"
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-linux-aarch64 -o ~/.docker/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
docker compose version || echo "Compose installation failed :("
