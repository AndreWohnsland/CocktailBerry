#!/bin/bash
# launcher.sh for both, maker and dashboard
# uncomment / comment the according lines

# launcher.sh for dashboard
# This for qt-app (recommended way)
# python3 /home/pi/Cocktailmaker_AW/dashboard/qt-app/main.py
# This for Dash (WebApp, advanced way)
# gunicorn --workers=5 --threads=1 -b :8050 index:server 

# launcher.sh for cocktailmaker
python3 /home/pi/Cocktailmaker_AW/runme.py