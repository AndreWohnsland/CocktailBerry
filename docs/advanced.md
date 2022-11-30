# Advanced Topics

Here you can find some advanced features of CocktailBerry, which you can optionally use.

## Usage of Services

Simply have `docker-compose` installed and run the command in the main folder for the CocktailBerry microservice or in the dashboard folder (on another device) for the dashboard service:

```
docker-compose up --build -d
```

This will handle the setup of all docker services. You will have to copy the `.env.example` file to `.env` and enter the needed secrets there for the container to work fully. If you are pulling for a later version, I recommend to run this command again, since the container may change in future version. 

There is now also the option to install directly from dockerhub, a GitHub action should build a new tag every release. Just visit [DockerHub](https://hub.docker.com/search?q=andrewo92) and pull the according images over docker or compose.

## Microservices

As a further addition since __version 1.1.0__, there is the option to run a microservice within docker which handles some networking topics. Cocktail data currently includes cocktail name, produced volume, current time, used language in config and your machines name.
Currently, this is limited to:

- Posting the cocktail data time to a given webhook
- Posting the cocktail data to the official dashboard API (__v1.7.0__), see [detailed description](#posting-data-to-the-official-api)
- Posting the export CSV as email to a receiver

The separation was made here that a service class within CocktailBerry needs only to make a request to the microservice endpoint. Therefore, all logic is separated to the service, and there is no need for multiple worker to not block the thread when the webhook endpoint is not up (Which would result in a delay of the display without multithreading). In the future, new services can be added easily to the docker container to execute different tasks. One example of the usage [can be found in my blog](https://andrewohnsland.github.io/blog/cocktail-maker-now-with-home-assistant). The service will also temporary store the data within a database, if there was no connection to the endpoint, and try later again. This way, no data will get lost in the void.

## Posting Data to the Official API

When the microservice is active, you can use it not to only to send data to your own webhook, but also to the official [CocktailBerry data API](https://github.com/AndreWohnsland/CocktailBerry-WebApp) to submit your data. It will then appear on the [official dashboard](https://stats-cocktailberry.streamlitapp.com/). Don't worry, no private data is included, only some production data. A detailed write down [can be found on the dashboard site](https://stats-cocktailberry.streamlitapp.com#how-to-participate) how you will receive your API key. You need to change the default `API_KEY` value in the `microservice/.env` file to the one you received after the submission. After that, your CocktailBerry will be able to also submit data and help populate the dashboard.

## Dashboard with Teams

With __version 1.2.0__, there is a team feature implemented into CocktailBerry. If enabled within the config, the user can choose one of two teams to book the cocktail and according volume to. The names of the teams, as well the URL of the dashboard device, can be specified within the config. CocktailBerry will then send the information to the Teams API. The Dashboard will use the API to display the current status in either amount of cocktails or volume of cocktails per team. In addition, there is the option to display all time data of the leader board. By default, the latest 24 hours, so mostly this party, will be shown. You should use a second device for the API / the dashboard for easy display on another screen.

<img src="../pictures/teams_ui.png" alt="Maker" width="600"/>

<img src="../pictures/dashboard.png" alt="Maker" width="600"/>

The **recommended way** is to use a second Raspberry Pi with a touchscreen attached. Then build the docker-compose file and execute the `dashboard/qt-app/main.py`. In before, you should install the `requirements.txt` within the same folder using pip. See [Usage of Services](#usage-of-services) how to set up docker-compose in general. The language can be set within the `dashboard/qt-app/.env` file, codes identical to [supported languages](languages.md#supported-languages). Just copy the `dashboard/qt-app/.env.example` file, rename the copy to `.env` and set your desired language. The easiest way is to use the provided shell script:


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

This will build up the backend API, as well as a Dash frontend Web App. Dash is using pandas, depending on your Raspberry Pi OS this installation it may run into issues, especially if running within the Docker container. You can then access the frontend over your browser at the RPi address over your network or over http://127.0.0.1:8050 from the Pi. If you are new to Python or programming, I strongly recommend using the first recommended option, since you will only lose the possibility to access the dashboard with multiple devices, like a smartphone.

In addition, if you want to automatically open the chromium browser on start, you can add the command to the autostart file:

```bash
echo "@chromium-browser --kiosk --app 127.0.0.1:8050" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
```

You can also set the second device up as a Wi-Fi hot-spot. This will give you the possibility to always connect to the dashboard, even if no connection to another home network or internet is available. For this, a very easy way is to use [RapsAp](https://raspap.com/).

## Installing Docker

tl;dr: Just run these commands in sequence on the pi and reboot after the first half.

```bash
sudo apt-get update && sudo apt-get upgrade
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker ${USER}
# reboot here or run sudo su - ${USER}
sudo apt-get install libffi-dev libssl-dev
sudo pip3 install docker-compose
sudo systemctl enable docker
# testing if it works
docker run hello-world
```

## Importing Recipes from File

With **version 1.10.0**, a new functionality to import batch recipe data was introduced.
You can now provide a `.txt` or similar text file to quickly insert a lot of new recipes, as well as ingredients.
To use this functionality, just use the CLI, similar to running CocktailBerry:

```bash
runme.py dataimport [OPTIONS] PATH

#   This will also be shown if you use the --help flag
#   Imports the recipe data from a file. If the units are not in ml, please
#   provide the conversion factor into ml.

#   The file should contain the cocktail name, followed by ingredient data
#   (amount, name). For further information regarding the file structure, please
#   see https://cocktailberry.readthedocs.io/advanced/#importing-recipes-from-
#   file.

# Arguments:
#   PATH  [required]

# Options:
#   -c, --conversion FLOAT  Conversion factor to ml  [default: 1.0]
#   -nu, --no-unit          Ingredient data got no unit text
#   --help                  Show this message and exit.
```

As usual, you can use the `--help` flag to get help on this functionality.
The data should be in the format:

```
Recipe Name1
Amount [unit] Ingredient1 Name
Amount [unit] Ingredient2 Name
...
Recipe Name2
Amount [unit] Ingredient1 Name
Amount [unit] Ingredient2 Name
```

You need to adjust the alcohol level, the bottle volume and hand add flag after the import, if there are new added ingredients.
The script will use a default of 0%, 1000 ml and not only handadd for each new ingredient.

The amount of newlines can be one or more between each line.
If there is another type of separator, please use a text editor to change it accordingly.
Also, if the recipe uses different types of units, please convert to the one provided by the conversion argument.
The script will check for duplicates and wait for user prompt, if there are any issues.
If the data got no unit between amount and name, use the `--no-unit` or `-nu` flag.
If the recipe use another unit than ml, please provide the according conversion factor, like `--conversion 29.5735` or `-c 29.5735`, when using oz.

I still **STRONGLY** recommend doing a backup of your local database (`Cocktail_database.db`) before running the import, just in case.
You can also use the build-in backup functionality in CocktailBerry for this.

*As a side note*: You should probably not mindlessly import a great amount of cocktails, because this will make the user experience of your CocktailBerry worse.
In cases of many ingredients, it's quite exhausting to select the right one. 
Having too many recipes active at once may also overwhelm your user, because there is too much to choose.
The recipes provided by default with CocktailBerry try to aim a good balance between the amount of cocktails, as well as a moderate common amount of ingredients within the singe cocktails.
This import function is limited by design, because batch import should only rarely (if even) happening, and some consideration and checking of the recipes should take place before doing so.


## Updating Local Database

With **version 1.10.0**, the CLI got the command to merge the latest recipes in your local database.
This can be useful if your CocktailBerry has been running for quite a while and you want to get more recipes.
The new recipes will be added to your database, including any missing ingredients.
Please take in consideration that if you made a lot of changes, especially renaming of your ingredients, this may add existing ingredients under a different name, since the names are in german.
It is best to make a backup before running the command, to have the possibility to restore the old state.
The script will also create a local backup, which you can use if you did not backup your data manually.
To update run the command:

```bash
python runme.py update-database
```

You can use the `--help` flag, like with the other commands, to get more insight into the command.