# Project Rules

- use the defined toolkit (e.g. uv, ruff, ty, yarn, biome) for dependency management and code quality
- Ensure tests are still succeeding after making a change, if a test exists
- Do not implement unasked extra features or edge cases, if you think they are crucial, you need to ask for permission first
- new dependencies need to work especially under unix (Raspberry Pi) systems

## App Versions

- **v1 (Qt)**: Desktop app using PyQt6, run via `runme.py` or `just qt`
- **v2 (Web)**: React frontend + FastAPI backend, run via `just api` + `just web`
- Unless specified otherwise, features should target both versions

## Project Structure

- `src/` - Main Python source (shared between v1/v2)
- `src/ui/` - Qt UI setup code (v1 only)
- `src/api/` - FastAPI routers & endpoints (v2 backend)
- `web_client/src/` - React components (v2 frontend)
- `tests/` - Pytest tests
- `dashboard/` - Separate analytics dashboard app

## Shared vs Version-Specific Code

Shared code (used by both v1 and v2):

- `src/database_commander.py` - Database operations
- `src/models.py` - Core data models
- `src/machine/` - Hardware control
- `src/config/` - Configuration handling

Version-specific code:

- `src/ui/` - Qt only (v1)
- `src/api/` - FastAPI only (v2)

## Configuration

- `src/config/` - Configuration management module
- `custom_config.yaml` - User customization file
- `web_client/.env.*` - Web client environment settings

## Singletons & Global State

Key modules use singletons — never instantiate new copies, always import the existing instance:

- **Via `__new__`**: `MachineController` (`src/machine/controller.py`), `NFCPaymentService` (`src/service/nfc_payment_service.py`)
- **Module-level instances**: `DB_COMMANDER` (`src/database_commander.py`), `CONFIG` / `shared` (`src/config/config_manager.py`), `DIALOG_HANDLER` (`src/dialog_handler.py`), `ADDONS` (`src/programs/addons.py`)

## Running Checks

- `just python-check` - ruff lint + format check + ty type check
- `just python-test` - pytest with coverage
- `just python-fix` - auto-fix lint and formatting
- `just web-lint` / `just web-format` - web client checks

## Translations

- **Python**: User-facing text uses `DialogHandler` with keys from `src/language.yaml`
- **Web client**: i18next with translation files in `web_client/src/locales/`

## Database

- SQLite + SQLAlchemy ORM, models in `src/db_models.py`
- Tests use in-memory SQLite (`sqlite:///:memory:`) via the `db_commander` fixture
