#!/bin/bash

export QT_SCALE_FACTOR=1
cd "$HOME/CocktailBerry/" || echo "Did not find ~/CocktailBerry/"
bash scripts/dependency_installer.sh
uv run --extra v1 --extra nfc runme.py
