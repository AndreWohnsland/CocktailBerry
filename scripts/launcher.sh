#!/bin/bash
# launcher.sh for both, machine and dashboard
# uncomment / comment the according lines

# launcher.sh for dashboard
# This for qt-app (recommended way)
# cd /home/pi/CocktailBerry/dashboard/qt-app/
# python3 main.py
# This for Dash (WebApp, advanced way)
# cd /home/pi/CocktailBerry/dashboard/frontend
# gunicorn --workers=5 --threads=1 -b :8050 index:server 

# launcher.sh for CocktailBerry
cd /home/pi/CocktailBerry/
python3 runme.py