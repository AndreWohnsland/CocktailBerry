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

# Function to create or update the virtual environment if necessary
create_or_update_venv() {
  system_python_version=$(python -V | awk '{print $2}')
  if [ -f ".venv/bin/python" ]; then
    venv_python_version=$(.venv/bin/python -V | awk '{print $2}')
  else
    venv_python_version=""
  fi

  if [ "$venv_python_version" != "$system_python_version" ]; then
    uv venv --system-site-packages --python "$system_python_version"
    echo "Virtual environment created/updated."
  else
    echo "Virtual environment is up-to-date."
  fi
}

# launcher.sh for CocktailBerry
export QT_SCALE_FACTOR=1
cd ~/CocktailBerry/ || echo "Did not find ~/CocktailBerry/"
create_or_update_venv
uv run --python "$(python -V | awk '{print $2}')" --all-extras runme.py
