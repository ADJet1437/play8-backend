# Poetry Setup Guide

This project uses Poetry for dependency management.

## Installation

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or on macOS with Homebrew:
```bash
brew install poetry
```

## Setup

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

   Or run commands with `poetry run`:
   ```bash
   poetry run uvicorn src.main:app --reload --port 8001
   ```

## Common Commands

### Add a new dependency:
```bash
poetry add package-name
```

### Add a development dependency:
```bash
poetry add --group dev package-name
```

### Update dependencies:
```bash
poetry update
```

### Show installed packages:
```bash
poetry show
```

### Export to requirements.txt (if needed):
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Running the Application

### With Poetry shell:
```bash
poetry shell
uvicorn src.main:app --reload --port 8001
```

### Without Poetry shell:
```bash
poetry run uvicorn src.main:app --reload --port 8001
```

## Development

The project structure:
- `pyproject.toml` - Poetry configuration and dependencies
- `poetry.lock` - Locked dependency versions (auto-generated, don't edit manually)
- `src/` - Source code

## Notes

- `requirements.txt` is kept for backward compatibility but Poetry is the primary dependency manager
- The virtual environment is managed by Poetry (usually in `~/.cache/pypoetry/virtualenvs/`)
- Ruff configuration is included in `pyproject.toml` under `[tool.ruff]`

