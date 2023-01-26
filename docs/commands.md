# CLI Commands

In this section, there is an overview and description of the Command Line Interface (CLI) commands of the program.
Within the CocktailBerry folder, you can execute them with the schema `python runme.py [command] [options]`.
There is also a `--help` flag to get information on the program, or it's sub-commands.
You can use this to get information on the commands when running locally.

## The Main Program

This is usually what you want to run.
The main program starts the CocktailBerry interface.
You can run it with:

```bash
python runme.py [OPTIONS]

```

You can run the calibration interface instead the usual main program when using the `-c` flag.
The calibration can also be accessed over the CocktailBerry interface (settings window).
If you want to debug your microservice, you ca activate the debug `-d` flag.
When debug is active, the data will be send to the **/debug** endpoint.
This endpoint will only log the payload (request.json), but not send it anywhere.
You can also show the program version, this is also shown at program start in the console.

## Updating Local Database

You can use the CLI command to merge the latest recipes in your local database.
To update run the command:

```bash
python runme.py [OPTIONS]

# Options:
#   -c, --calibration  Run the calibration program.
#   -d, --debug        Using debug instead of normal Endpoints.
#   --version          Show current version.
#   --help                  Show help
```

This can be useful if your CocktailBerry has been running for quite a while and you want to get more recipes.
The new recipes will be added to your database, including any missing ingredients.

!!! warning "Made many Changes?"
    Please take in consideration that if you made a lot of changes, especially renaming your ingredients, this may add existing ingredients under a different name.
    It is best to make a backup before running the command, to have the possibility to restore the old state.
    The script will also create a local backup, which you can use if you did not backup your data manually.

## Clearing Local Database

There may be CocktailBerry owners, who want to create a complete new database.
To clean the local database, run:

```bash
python runme.py clear-database [OPTIONS]

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
python runme.py dataimport [OPTIONS] PATH

# Arguments:
#   PATH  [required]

# Options:
#   -c, --conversion FLOAT  Conversion factor to ml  [default: 1.0]
#   -nu, --no-unit          Ingredient data got no unit text
#   --help                  Show help
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

!!! warning "Safety First"
    I still **STRONGLY** recommend doing a backup of your local database (`Cocktail_database.db`) before running the import, just in case.
    You can also use the build-in backup functionality in CocktailBerry for this.

!!! info "As a Side Note"
    You should probably not mindlessly import a great amount of cocktails, because this will make the user experience of your CocktailBerry worse.
    In cases of many ingredients, it's quite exhausting to select the right one. 
    Having too many recipes active at once may also overwhelm your user, because there is too much to choose.
    The recipes provided by default with CocktailBerry try to aim a good balance between the amount of cocktails, as well as a moderate common amount of ingredients within the single cocktails.
    This import function is limited by design, because batch import should only rarely (if even) happening, and some consideration and checking of the recipes should take place before doing so.
