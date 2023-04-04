# Advanced Topics

Here you can find some advanced features of CocktailBerry, which you can optionally use.
Take note that none of this section is required to run the base program.

!!! example "Use the CLI"
    The latest and easiest way to install the CocktailBerry microservice is over the [CLI](commands.md#setup-the-microservice).
    Just run:
    ```bash
    python runme.py setup-microservice
    ```
    for the interactive mode to change the env variables and build the service including automated updates.

## Usage of Services

Simply have `docker-compose` installed and run the command in the main folder for the CocktailBerry microservice or in the dashboard folder (on another device) for the dashboard service:

```
docker-compose up --build -d
```

!!! info "Newer Compose Version"
    You may need to type `docker compose` instead of `docker-compose` at the latest (v2) version of compose.

This will handle the setup of all docker services.
You will have to copy the `.env.example` file to `.env` and enter the needed secrets there for the container to work fully.
If you are pulling for a later version, I recommend to run this command again, since the container may change in future version. 

!!! tip "Try the Pre-build Image"
    There is now also the option to install directly from DockerHub, a GitHub action should build a new tag every release.
    Just visit [DockerHub](https://hub.docker.com/search?q=andrewo92) and pull the according images over docker or compose and follow the instruction on DockerHub.
    Best is to create the according `docker-compose.yaml` file on your desktop, or anywhere outside the project, since you enter your personal credentials there.
    Building from DockerHub is probably faster and easier, but using the local self build instruction will also work.

## Microservices

As a further addition, there is the option to run a microservice within docker which handles some networking topics.
Cocktail data currently includes cocktail name, produced volume, ingredients, current time, used language in config and your machines name.
Currently, this is limited to:

- Posting the cocktail data time to a given webhook, adding header information
- Posting the cocktail data to the official dashboard API, see [detailed description](#posting-data-to-the-official-api)

!!! info
    This is optional, if you don't want this feature, you don't need the microservice.

The separation was made here that a service class within CocktailBerry needs only to make a request to the microservice endpoint.
Therefore, all logic is separated to the service, and there is no need for multiple worker to not block the thread when the webhook endpoint is not up (Which would result in a delay of the display without multithreading).
In the future, new services can be added easily to the docker container to execute different tasks.
One example of the usage [can be found in my blog](https://andrewohnsland.github.io/blog/cocktailberry-now-with-home-assistant).
The service will also temporary store the data within a database, if there was no connection to the endpoint, and try later again.
This way, no data will get lost in the void.

## Posting Data to the Official API

When the microservice is active, you can use it not to only to send data to your own webhook, but also to the official [CocktailBerry data API](https://github.com/AndreWohnsland/CocktailBerry-WebApp) to submit your data.
It will then appear on the [official dashboard](https://stats-cocktailberry.streamlitapp.com/).
Don't worry, no private data is included, only some production data.
A detailed write down [can be found on the dashboard site](https://stats-cocktailberry.streamlitapp.com#how-to-participate) how you will receive your API key.
You need to change the default `API_KEY` value in the `microservice/.env` file to the one you received after the submission.
After that, your CocktailBerry will be able to also submit data and help populate the dashboard.

## Dashboard with Teams

There is a team feature implemented into CocktailBerry.
If enabled within the config, the user can choose one of two teams to book the cocktail and according volume to.
The names of the teams, as well the URL of the dashboard device, can be specified within the config.
CocktailBerry will then send the information to the teams API.
The Dashboard will use the API to display the current status in either amount of cocktails or volume of cocktails per team.
In addition, there is the option to display all time data of the leader board.
By default, the latest 24 hours, so mostly this party, will be shown.
You should use a second device for the API / the dashboard for easy display on another screen.

<figure markdown>
  ![Teamselection](pictures/teams_ui.png)
  <figcaption>Teams Selection in CocktailBerry</figcaption>
</figure>

<figure markdown>
  ![Team_dashboard](pictures/dashboard.png)
  <figcaption>Dashboard View for Teams</figcaption>
</figure>

The **recommended way** is to use a second Raspberry Pi with a touchscreen attached.
Then build the docker-compose file and execute the `dashboard/qt-app/main.py`.
In before, you should install the `requirements.txt` within the same folder using pip.
See [Usage of Services](#usage-of-services) how to set up docker-compose in general.
The language can be set within the `dashboard/qt-app/.env` file, codes identical to [supported languages](languages.md).
Just copy the `dashboard/qt-app/.env.example` file, rename the copy to `.env` and set your desired language.
The easiest way is to use the provided shell script:

```bash
sh scripts/setup.sh dashboard
```

Or you can set it up yourself:

```bash
cd dashboard
docker-compose up --build -d
cd qt-app
pip install -r requirements.txt
cp .env.example .env
python main.py
```

A **second option** is to use either the `docker-compose.both.yaml` file with the docker-compose `--file` option, or to use the other provided frontend:

```bash
# Either both in docker
cd dashboard
cp frontend/.env.example frontend/.env
docker-compose -f docker-compose.both.yaml up --build -d
# or API in Docker, frontend over RPi CLI
cd dashboard
docker-compose up --build -d
cd frontend
pip install -r requirements.txt
cp .env.example .env
python index.py
```

This will build up the backend API, as well as a Dash frontend Web App.
Dash is using pandas, depending on your Raspberry Pi OS this installation it may run into issues, especially if running within the Docker container.

You can then access the frontend over your browser at the RPi address over your network or over http://127.0.0.1:8050 from the Pi. 
If you are new to Python or programming, I strongly recommend using the first recommended option, since you will only lose the possibility to access the dashboard with multiple devices, like a smartphone.

!!! tip "Easy and Fast"
    Both of these images are also available at [DockerHub](https://hub.docker.com/search?q=andrewo92), so if you want to avoid build issues, you can just use the pre-build image.
    Again, create the according `docker-compose.yaml` file on your desktop, or in a separate location.

In addition, if you want to automatically open the chromium browser on start, you can add the command to the autostart file:

```bash
echo "@chromium-browser --kiosk --app 127.0.0.1:8050" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
```

You can also set the second device up as a Wi-Fi hot-spot.
This will give you the possibility to always connect to the dashboard, even if no connection to another home network or internet is available.
For this, a very easy way is to use [RapsAp](https://raspap.com/).

## Installing Docker

tl;dr: Just run these commands in sequence on the pi.

```bash
sudo apt-get update && sudo apt-get -y upgrade
sudo apt install docker.io -y
docker --version || echo "Docker installation failed :("
sudo usermod -aG docker $USER
newgrp docker
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-linux-aarch64 -o ~/.docker/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
docker compose version || echo "Compose installation failed :("
docker run hello-world
```

!!! info "Less Typing"
    Using the included script `sh scripts/install_docker.sh` and `sh scripts/install_compose.sh` will also do that for you.
    You may have executed it at the setup of you CocktailBerry and therefore already installed docker.
