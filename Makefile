VENV_PYTHON := $(wildcard venv/bin/python)
ifeq ($(VENV_PYTHON),)
    PYTHON ?= python3
else
    PYTHON := $(VENV_PYTHON)
endif

.PHONY: dev-start validate service-status start-services stop-services \
    health-check health-monitor wait-for-mcp ai-review-changes \
    before-ai-coding after-ai-coding restart-services format lint clean-code

dev-start:
	bash start_orchestra.sh

validate:
	$(PYTHON) scripts/ai_code_reviewer.py --check-all

service-status:
	$(PYTHON) scripts/orchestra.py status

start-services:
	$(PYTHON) scripts/orchestra.py start

stop-services:
	$(PYTHON) scripts/orchestra.py stop

restart-services: stop-services start-services

health-check:
	$(PYTHON) scripts/orchestra.py health

health-monitor:
	$(PYTHON) scripts/health_monitor.py --monitor

wait-for-mcp:
	$(PYTHON) scripts/health_monitor.py --wait-for orchestrator

ai-review-changes:
	$(PYTHON) scripts/ai_code_reviewer.py --check-changes

before-ai-coding:
	git add -A && git commit -m "checkpoint: before AI coding session" && $(PYTHON) scripts/orchestra.py status > pre-ai-status.txt

after-ai-coding:
	$(MAKE) ai-review-changes
	$(MAKE) validate

vultr-deploy:
	$(PYTHON) scripts/vultr_provision.py $(ARGS)

# Code formatting commands
format:
	@echo "🎨 Formatting code with Black and isort..."
	@black . --quiet
	@isort . --quiet

format-safe:
	@echo "🎨 Formatting code (excluding known issues)..."
	@black . --quiet --extend-exclude "shared/database/decorators.py|shared/memory/unified_postgresql_weaviate.py|shared/database/unified_db_v2.py"
	@isort . --quiet --skip shared/database/decorators.py --skip shared/memory/unified_postgresql_weaviate.py --skip shared/database/unified_db_v2.py

lint:
	@echo "🔍 Running linters..."
	@flake8 .
	@echo "✅ Linting complete"

clean-code: format lint
	@echo "✨ Code is clean and formatted!"
