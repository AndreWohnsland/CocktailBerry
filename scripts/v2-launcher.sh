#!/bin/bash

cd "$HOME/CocktailBerry/" || echo "Did not find ~/CocktailBerry/"
uv run --extra nfc api.py
