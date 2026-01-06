# CLI Commands

In this section, there is an overview and description of the Command Line Interface (CLI) commands of the program.
Within the CocktailBerry folder, you can execute them with the schema `uv run runme/api.py [command] [options]`.
There is also a `--help` flag to get information on the program, or it's sub-commands.
You can use this to get information on the commands when running locally.

!!! info "Used Auto Setup?"
    If you installed over the setup script, the program will usually started over the `~/launcher.sh` file.
    When you want to use other than the default options, change the `~/launcher.sh` file accordingly.
    Just add the flags or their according values to the `uv run runme.py` command.

!!! info "v1 or v2?"
    If you are already running the API (v2) version, you need to use the command `api.py` instead of `runme.py`.
    Everything else (like the options) is the same.
    Also, if you are on the latest version, you should use `uv run ...` instead of `python ...`.

## The Main Program

This is usually what you want to run.
The main program starts the CocktailBerry interface.
You can run it with:

```bash
uv run runme.py [OPTIONS]

# Options:
#   -n, --name TEXT    Name to display at start.  [default: CocktailBerry]
#   -q, --quiet        Hide machine name, version and platform data.
#   -d, --debug        Using debug instead of normal Endpoints.
#   -V, --version      Show current version.
#   --help             Show help
```

If you want to debug your microservice, you ca activate the debug `-d` flag.
When debug is active, the data will be send to the **/debug** endpoint.
This endpoint will only log the payload (request.json), but not send it anywhere.
You can also show the program version, this is also shown at program start in the console.
In addition, you may want to display another name than CocktailBerry, which is the default.
Use the `-n` option, like `-n "YourName"`, to set a custom name.
If you want omit the machine name, version and platform data, use the `-q` flag.

In case you want to hide the terminal completely, see [this section](faq.md#how-to-minimize-start-terminal).

## CocktailBerry Web

Run the FastAPI web server (for v2).
Can be used as an alternative way to control the machine, for example over an external program or a web ui. The FastAPI server will be started at the given port.

```bash
uv run api.py [OPTIONS]

# Options:
#   -p, --port INTEGER  Port for the FastAPI server [default: 8000]
#   --help              Show help
```

## Switch to CocktailBerry Web

This command will set up the web interface as the default interface.
Take care, this wil no longer start the main program, but the web interface.
The web interface will then be accessible over a web browser, which will be opened in Kiosk mode on the machine.
If you want to access the web interface from another device, you can open the browser and navigate to `http://<ip>` or locally on `http://localhost`.
You can also set up SSL, this is only necessary if you want to manage backups over another device and not directly on the machine.
This is the limitation sending files over the network, which is not possible without SSL.
If SSL is enabled, since this is a self-signed certificate, you will get a warning in the browser, which user can ignore.

```bash
uv run runme.py setup-web

# Options:
#   --ssl   -s        Use SSL for the Nginx configuration    
#   --help            Show help
```

## Switch to old Main Program (v1)

In case you activated the web interface as the default interface, you can switch back to the old main program.
This command will switch back to the old main program.
This will no longer start the web interface, but the main program.
The main program will then be started as usual as an full windowed app.

```bash
uv run runme.py switch-back
```

## Clearing Local Database

There may be CocktailBerry owners, who want to create a complete new database.
To clean the local database, run:

```bash
uv run runme.py clear-database [OPTIONS]

# Options:
#   --help  Show help
```

This command will delete all recipes and ingredients from the local database.
Before that, a local backup is created, in case you want a rollback.
You can then either enter new recipes over the interface, or import your recipes from a file (see below).

## Importing Recipes from File

You can use this functionality to import batch recipe data.
You can now provide a `.txt` or similar text file to quickly insert a lot of new recipes, as well as ingredients.
To use this functionality, just use the CLI, similar to running CocktailBerry:

```bash
uv run runme.py data-import [OPTIONS] PATH

# Arguments:
#   PATH  [required]

# Options:
#   -c, --conversion FLOAT  Conversion factor to ml  [default: 1.0]
#   -nu, --no-unit          Ingredient data got no unit text
#   --help                  Show help
```

As usual, you can use the `--help` flag to get help on this functionality.
The data should be in the format:

```txt
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

!!! danger "Safety First"
    I still **STRONGLY** recommend doing a backup of your local database (`Cocktail_database.db`) before running the import, just in case.
    You can also use the build-in backup functionality in CocktailBerry for this.

!!! note "As a Side Note"
    You should probably not mindlessly import a great amount of cocktails, because this will make the user experience of your CocktailBerry worse.
    In cases of many ingredients, it's quite exhausting to select the right one.
    Having too many recipes active at once may also overwhelm your user, because there is too much to choose.
    The recipes provided by default with CocktailBerry try to aim a good balance between the amount of cocktails, as well as a moderate common amount of ingredients within the single cocktails.
    This import function is limited by design, because batch import should only rarely (if even) happening, and some consideration and checking of the recipes should take place before doing so.

## Creating Addon Base File

Use this command to get starting developing your own addon!

```bash
uv run runme.py create-addon [OPTIONS] ADDON_NAME

# Arguments:
#   ADDON_NAME  [required]

# Options:
#   --help  Show help
```

Creates a file containing the base structure to get started with your addon.
The file is placed in the `addons` folder.
File name will be the name converted to lower case, space are replaced with underscores and stripped of special characters.

## Setup the Microservice

You can also use CocktailBerry to set up the [microservice](advanced.md#cocktailberry-microservice) and change the env variables.
It uses the latest image from Dockerhub.
With the microservice, also [watchtower](https://containrrr.dev/watchtower/) will be deployed.
Watchtower will check periodically if there is a new microservice image and install it in the background.

```bash
uv run runme.py setup-microservice [OPTIONS]

# Options:
#   -a, --api-key TEXT        API key for dashboard
#   -e, --hook-endpoint TEXT  Custom hook endpoint
#   -h, --hook-header TEXT    Custom hook headers
#   -o, --old-compose         Use compose v1
#   --help                    Show help
```

Set up the microservice.
If the API key, hook endpoint or hook header is not provided as an option, prompts the user for the values.
Within the prompts, you can reset the value to the default one, or also skip this value if it should not be changed.
A compose file will be created in the home directory, if this command was not already run once.
If this file already exists, the values will be replaced with the provided ones.

!!! danger "For Docker Compose V2"
    Please take note that this command is programmed for docker compose v2.
    It's currently the default compose and the CocktailBerry setup will also install it.
    If you are still running v1 (docker-compose), consider upgrading.
    In case you are using v1, add the `-o` or `--old-compose` flag.

## Setup the Teams Dashboard

You can also use CocktailBerry to set up the [Teams Dashboard](advanced.md#dashboard-with-teams).
It uses the latest image from Dockerhub.
With the dashboard, also [watchtower](https://containrrr.dev/watchtower/) will be deployed.
Watchtower will check periodically if there is a new dashboard image and install it in the background.

```bash
uv run runme.py setup-teams-service [OPTIONS]

# Options:
#   -l, --language [en|de]  language for the teams service  [default: en]
#   --help                  Show help
```

Set up the teams microservice. You can use english (en) or german (de) as language.
Will run the frontend at `localhost:8050` (http://127.0.0.1:8050), backend at `localhost:8080` (http://127.0.0.1:8080).

## Create an Access Point

You can also use CocktailBerry to set up an access point.
The access point will be crated on a virtual wlan1 interface.
So you can still use the wlan0 interface for your normal network connection.
This requires that you can have a virtual interface on your chip, for example the Raspberry Pi 3B+.

```bash
uv run runme.py setup-ap [OPTIONS]

# Options:
#   --ssid      SSID Name of the AP [default: CocktailBerry]
#   --password  Password of the AP [default: cocktailconnect]
#   --help      Show help
```

## Remove the Access Point

If you want to remove the access point, you can use this.

```bash
uv run runme.py remove-ap [OPTIONS]

# Options:
#   --ssid      SSID Name of the AP [default: CocktailBerry]
#   --help      Show help
```
