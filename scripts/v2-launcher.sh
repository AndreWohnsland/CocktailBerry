#!/bin/bash
cd "$HOME/CocktailBerry/" || echo "Did not find ~/CocktailBerry/"
uv run api.py --extra nfc
