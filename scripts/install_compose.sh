#!/bin/bash

echo "Installing Compose"
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
if $(uname -m | grep '64'); then
  echo "Detected 64 bit system, using aarch64 compose image"
  curl -SL https://github.com/docker/compose/releases/download/v2.19.1/docker-compose-linux-aarch64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
else
  echo "Detected 32 bit system, using armv7l compose image"
  curl -SL https://github.com/docker/compose/releases/download/v2.19.1/docker-compose-linux-armv7 -o $DOCKER_CONFIG/cli-plugins/docker-compose
fi
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
docker compose version || echo "Compose installation failed :("
