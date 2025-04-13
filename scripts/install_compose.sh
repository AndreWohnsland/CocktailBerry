#!/bin/bash

echo "> Installing Compose"
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p "$DOCKER_CONFIG/cli-plugins"
# in the future, sudo apt install docker-compose-plugin should work
# sadly, this still does not work :(

# we gonna use a virtual environment because thats the way on bookworm
# and use lastversion to get the latest version url from the docker compose GitHub
# This is used to have always the latest version and not a fixed one
echo "> Creating temporary virtual environment for lastversion"
python -m venv --system-site-packages ~/.env-compose
# shellcheck disable=SC1090
source ~/.env-compose/bin/activate
echo "Installing lastversion"
pip install -q lastversion

# You could get the version number and just use it in the URL string
# COMPOSE_VERSION=$(lastversion docker/compose)
# but its more robust to get the whole asset URL

if [ "$(getconf LONG_BIT)" = "64" ]; then
  echo "> Detected 64 bit system, using aarch64 compose image"
  DOWNLOAD_URL=$(lastversion --assets --filter '\-linux-aarch64$' docker/compose)
else
  echo "> Detected 32 bit system, using armv7l compose image"
  DOWNLOAD_URL=$(lastversion --assets --filter '\-linux-armv7l$' docker/compose)
fi
curl -SL "$DOWNLOAD_URL" -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
docker compose version || echo "Compose installation failed :("

# remove venv at the end
echo "> remove temporary virtual environment"
deactivate
rm -rf ~/.env-compose
