#!/bin/bash
# launcher.sh for both, machine and dashboard
# uncomment / comment the according lines

# launcher.sh for dashboard
# This for qt-app (recommended way)
# cd ~/CocktailBerry/dashboard/qt-app/
# python3 main.py  &>> ~/CocktailBerry/logs/shelllogs.txt  
# This for Dash (WebApp, advanced way)
# cd ~/CocktailBerry/dashboard/frontend/
# gunicorn --workers=5 --threads=1 -b :8050 index:server 

# launcher.sh for CocktailBerry
cd ~/CocktailBerry/
python3 runme.py &>> ~/CocktailBerry/logs/shelllogs.txt