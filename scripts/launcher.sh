#!/bin/bash
# launcher.sh for both, machine and dashboard
# uncomment / comment the according lines

# launcher.sh for dashboard
# This for qt-app (recommended way)
# cd ~/CocktailBerry/dashboard/qt-app/
# python main.py
# This for Dash (WebApp, advanced way)
# cd ~/CocktailBerry/dashboard/frontend/
# gunicorn --workers=5 --threads=1 -b :8050 index:server

# launcher.sh for CocktailBerry
export QT_SCALE_FACTOR=1
cd ~/CocktailBerry/ || echo "Did not find ~/CocktailBerry/" && exit
python runme.py
