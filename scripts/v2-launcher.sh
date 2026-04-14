#!/bin/bash

cd "$HOME/CocktailBerry/" || echo "Did not find ~/CocktailBerry/"
bash scripts/dependency_installer.sh
uv run --extra nfc api.py
