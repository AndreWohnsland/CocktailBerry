# CocktailBerry Justfile
# See https://just.systems/man/en/ for documentation

# Use PowerShell on Windows
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Global variables
qt_ui_files := "available bonusingredient bottlewindow cocktailmanager calibration calibration_real calibration_target customdialog datepicker keyboard optionwindow numpad progressbarwindow teamselection passworddialog customprompt logwindow rfidwriter wifiwindow customcolor addonwindow addonmanager datawindow cocktail_selection picture_window refill_prompt config_window resource_window news_window sumup_reader_window"

# Install all Python dependencies (main + dev)
[group('Python Environment & Dependencies')]
install:
    uv sync

# Install Python dependencies for v1 (Qt) with optional NFC support
[group('Python Environment & Dependencies')]
install-v1 nfc="false":
    @if {{nfc}} == "true" { uv sync --extra v1 --extra nfc } else { uv sync --extra v1 }

# Install Python dependencies for NFC support
[group('Python Environment & Dependencies')]
install-nfc:
    uv sync --extra nfc

# Install web client dependencies
[group('Python Environment & Dependencies')]
install-web:
    cd web_client && yarn install

# Install dashboard dependencies
[group('Python Environment & Dependencies')]
install-dashboard:
    cd dashboard && uv sync

# Install all project dependencies (Python with all extras, web, dashboard)
[group('Python Environment & Dependencies')]
install-all:
    uv sync --all-extras
    cd web_client && yarn install

# Run the main CocktailBerry Qt application (v1)
[group('Running Applications')]
qt:
    uv run runme.py

# Run the FastAPI backend server (development mode)
[group('Running Applications')]
api:
    uv run fastapi dev ./src/api/api.py

# Run the web client development server
[group('Running Applications')]
web:
    cd web_client && yarn dev

# Run the dashboard backend
[group('Running Applications')]
dashboard-backend:
    cd dashboard/backend && uv run main.py

# Run the dashboard frontend
[group('Running Applications')]
dashboard-frontend:
    cd dashboard/frontend && uv run index.py

# Compile all Qt UI files to Python
[unix, group('Qt UI Development')]
qt-compile:
    @echo "Compiling Qt UI files, this might take some seconds..."
    @cd src/ui_elements && \
    for f in {{qt_ui_files}}; do \
        uv run pyuic6 -x ./$f.ui -o ./$f.py; \
    done

# Compile Qt UI files (Windows PowerShell version)
[windows, group('Qt UI Development')]
qt-compile:
    @echo "Compiling Qt UI files, this might take some seconds..."
    @$files = "{{qt_ui_files}}" -split ' '; Push-Location src/ui_elements; foreach ($f in $files) { uv run pyuic6 -x "$f.ui" -o "$f.py" }; Pop-Location

# Open Qt Designer for UI editing
[group('Qt UI Development')]
qt-designer:
    uv run pyqt6-tools designer

# Compile SCSS styles to QSS
[group('Qt UI Development')]
qt-styles:
    uv run qtsass ./src/ui/styles/ -o ./src/ui/styles/

# Build the web client for production
[group('Web Client')]
web-build:
    cd web_client && yarn build

# Build the web client for demo
[group('Web Client')]
web-build-demo:
    cd web_client && yarn build-demo

# Fix web client linting issues
[group('Web Client')]
web-lint:
    cd web_client && yarn lint:fix

# Fix web client formatting issues
[group('Web Client')]
web-format:
    cd web_client && yarn format:fix

# Fix all web client issues
[group('Web Client')]
web-check:
    cd web_client && yarn check:fix

# Run Storybook for component development
[group('Web Client')]
web-storybook:
    cd web_client && yarn storybook

# Build Storybook
[group('Web Client')]
web-storybook-build:
    cd web_client && yarn build-storybook

# Preview the built web client
[group('Web Client')]
web-preview:
    cd web_client && yarn preview

# Run all Python code quality checks (lint, format, typecheck)
[group('Code Quality')]
python-check:
    uv run ruff check ./src
    uv run ruff format ./src --check
    uv run ty check ./src

# Fix all auto-fixable Python issues (lint + format)
[group('Code Quality')]
python-fix:
    uv run ruff check ./src --fix
    uv run ruff format ./src

# Run tests with coverage report
[group('Testing')]
python-test:
    uv run pytest --cov --cov-report=html

# Serve documentation locally
[group('Documentation')]
docs:
    uv run mkdocs serve

# Build documentation
[group('Documentation')]
docs-build:
    uv run mkdocs build

# Install pre-commit hooks
[group('Pre-commit & CI')]
pre-commit-install:
    uv run pre-commit install

# Run pre-commit on all files
[group('Pre-commit & CI')]
pre-commit:
    uv run pre-commit run --all-files

# Full CI check (python-check + test)
[group('Pre-commit & CI')]
ci: python-check python-fix python-test web-lint web-format

# Run database migrations
[group('Database')]
db-migrate:
    uv run alembic upgrade head

# Create a new migration
[group('Database')]
db-migration-new name:
    uv run alembic revision --autogenerate -m "{{name}}"

# Build and start main docker services
[group('Docker')]
docker-up:
    docker compose up --build --detach

# Stop docker services
[group('Docker')]
docker-down:
    docker compose down

# Build and start microservice
[group('Docker')]
microservice-up:
    cd microservice && docker compose -f docker-compose.local.yaml up --build --detach

# Stop microservice
[group('Docker')]
microservice-down:
    cd microservice && docker compose -f docker-compose.local.yaml down

# Build and start dashboard services
[group('Docker')]
dashboard-up:
    cd dashboard && docker compose -f docker-compose.both.yaml up --build --detach

# Stop dashboard services
[group('Docker')]
dashboard-down:
    cd dashboard && docker compose -f docker-compose.both.yaml down
