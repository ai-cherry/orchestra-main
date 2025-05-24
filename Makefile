# Unified Makefile for Python Project (pip-based)
# Usage: make <target>
# Ensures robust, reproducible, and efficient workflows for a single-developer project.

# --- Environment Checks ---
venv-check:
	@python scripts/check_venv.py

deps-check:
	@python scripts/check_dependencies.py

outdated:
	@python scripts/check_dependencies.py --show-outdated

# --- Dependency Management ---
install:
	@pip install --upgrade pip
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	@if [ -f orchestrator/requirements.txt ]; then pip install -r orchestrator/requirements.txt; fi
	@if [ -f requirements/dev.txt ]; then pip install -r requirements/dev.txt; fi

# install only prod deps
install-prod:
	@pip install --upgrade pip
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# dev install explicitly
install-dev: install  ## Install prod and dev dependencies

update:
	@pip install --upgrade pip
	@pip list --outdated
	@echo "Update your requirements.txt as needed and re-run 'make install'"

# --- Linting, Formatting, Type-Checking ---
lint:
	@flake8 .
	@ruff check .

format:
	@black .
	@ruff format .

type-check:
	@mypy .

# --- Testing ---
test:
	@pytest

# --- Pre-commit Hooks ---
pre-commit-run:
	@pre-commit run --all-files

# --- All-in-One Validation ---
validate: venv-check deps-check lint type-check test pre-commit-run

.PHONY: venv-check deps-check outdated install update lint format type-check test pre-commit-run validate
