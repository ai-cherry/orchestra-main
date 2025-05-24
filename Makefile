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
validate: venv-check deps-check lint type-check test pre-commit-run config-validate

# Orchestra automation targets
.PHONY: config-validate health-check start-services stop-services monitor

# Configuration validation (renamed to avoid conflict)
config-validate:
	@echo "🔍 Running comprehensive validation..."
	python scripts/config_validator.py --verbose
	python scripts/health_monitor.py --check-prereqs

# Health monitoring
health-check:
	@echo "🏥 Checking service health..."
	python scripts/health_monitor.py --check-services

health-monitor:
	@echo "🔄 Starting health monitoring..."
	python scripts/health_monitor.py --monitor --interval=30

# Service management
start-services:
	@echo "🚀 Starting Orchestra services..."
	python scripts/orchestra.py services start

stop-services:
	@echo "🛑 Stopping Orchestra services..."
	python scripts/orchestra.py services stop

service-status:
	@echo "📊 Checking service status..."
	python scripts/orchestra.py services status

# Environment setup
env-setup:
	@echo "🛠️ Setting up environment..."
	python scripts/orchestra.py env setup

# Unified CLI alias
orchestra:
	@echo "🎼 Orchestra CLI - Use: make orchestra ARGS='command'"
	python scripts/orchestra.py $(ARGS)

# Wait for services to be ready (replaces sleep)
wait-for-mcp:
	@echo "⏳ Waiting for MCP services..."
	python scripts/health_monitor.py --wait-for mcp_secret_manager --max-wait 60
	python scripts/health_monitor.py --wait-for mcp_firestore --max-wait 60

# Combined startup with health checks
start-and-validate: start-services wait-for-mcp health-check
	@echo "✅ Services started and validated"

# Development workflow
dev-start: env-setup config-validate start-and-validate
	@echo "🎯 Development environment ready!"

# Production deployment validation
deploy-validate: config-validate health-check
	@echo "✅ Ready for deployment"

# AI Code Review targets
.PHONY: ai-review ai-review-changes ai-review-scan

# Review AI-generated code changes
ai-review-changes:
	@echo "🤖 Reviewing AI code changes..."
	python scripts/ai_code_reviewer.py --check-changes

# Full project scan for AI anti-patterns  
ai-review-scan:
	@echo "🔍 Scanning project for AI anti-patterns..."
	python scripts/ai_code_reviewer.py --full-scan

# Review specific file
ai-review:
	@echo "📄 Reviewing file: $(FILE)"
	@if [ -z "$(FILE)" ]; then echo "Usage: make ai-review FILE=path/to/file.py"; exit 1; fi
	python scripts/ai_code_reviewer.py --check-file $(FILE)

# Pre-AI coding preparation
before-ai-coding:
	@echo "🎯 Preparing for AI coding session..."
	@echo "Creating checkpoint..."
	@git add -A && git commit -m "checkpoint: before AI coding session" || true
	@echo "Documenting current state..."
	@python scripts/orchestra.py services status > .ai-session/pre-status.txt || true
	@pip freeze > .ai-session/pre-requirements.txt || true
	@echo "Current tool inventory:"
	@ls -la scripts/*.py | grep -v __pycache__
	@echo ""
	@echo "Ready for AI coding! Remember:"
	@echo "- Python 3.10 (not 3.11+)"
	@echo "- pip/venv only (no Poetry/Docker)"
	@echo "- Check scripts/ for existing tools"
	@echo "- Keep it simple!"

# Post-AI coding validation
after-ai-coding: ai-review-changes validate
	@echo "✅ AI coding session validated"

.PHONY: venv-check deps-check outdated install update lint format type-check test pre-commit-run validate
