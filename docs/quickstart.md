# Quickstart

Here are some simple steps to get CocktailBerry running.
You need to have [uv](https://docs.astral.sh/uv/getting-started/installation/) (or Python 3.13+) and [**git**](https://git-scm.com/downloads) installed.
If you want to use v2 in a manual installation, you also need to have [Node.js](https://nodejs.org/en/download/) and [Yarn](https://yarnpkg.com/getting-started/install) installed.

## Raspberry Pi

--8<-- "all_in_one.md"

Now you can [Set Up](setup.md#setting-up-the-machine-modifying-other-values) your CocktailBerry and tweak the settings to your liking.
If you want to have the new v2 API and app, see [web setup](web.md) for how to easily switch after the setup.
Or add a `-s v2` at the end of the command to execute the switch directly after installing.

## Other OS or Development Setup

First clone the repository:

```bash
cd ~
git clone https://github.com/AndreWohnsland/CocktailBerry.git
cd CocktailBerry
```

Then choose which version you want to install.

### V1 (PyQt Application)

```bash
uv sync --extra v1 # and --extra nfc if you want NFC support
uv run runme.py
```

### V2 (API and Web Client)

```bash
uv sync # and --extra nfc if you want NFC support
uv run api.py
```

Second terminal for the web client:

```bash
cd ~/CocktailBerry/web_client
yarn install
yarn dev
```

This will start the CocktailBerry program.
See [Installation](installation.md) for more information.
