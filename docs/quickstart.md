# Quickstart

Here are some simple steps to get CocktailBerry running.
You need to have [**Python 3.9**](https://www.python.org/downloads/) or newer and [**git**](https://git-scm.com/downloads) installed.

## Raspberry Pi

!!! tip "RPi: Try the all in one Script"
    If you are on your Raspberry Pi, you can just use the so called *All In One Script*!
    This will check that git, Python and your OS are compatible for the project and install CocktailBerry including Docker and Compose on the Pi.
    
    Just use:

    ```bash
    wget -O - https://raw.githubusercontent.com/AndreWohnsland/CocktailBerry/master/scripts/all_in_one.sh | bash
    ```
    to get the script and run it on the Pi. To easy to be true, isn't it?

Now you can [Set Up](setup.md#setting-up-the-machine-modifying-other-values) your CocktailBerry and tweak the settings to your liking.
If you want to have the new v2 API and app, see [web setup](web.md) how to easily switch after the setup.

## Other OS

For a peak into the project run:

```bash
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd CocktailBerry
pip install -r requirements.txt
# you can get help with python runme.py --help
python runme.py
```

This will start the CocktailBerry program.
You may want to run the provided installer script for the Raspberry Pi instead of pip.
See [Installation](installation.md) for more information.

```bash
sh scripts/setup.sh
```
