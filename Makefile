VENV_PYTHON := $(wildcard venv/bin/python)
ifeq ($(VENV_PYTHON),)
    PYTHON ?= python3
else
    PYTHON := $(VENV_PYTHON)
endif

.PHONY: dev-start validate service-status start-services stop-services \
    health-check health-monitor wait-for-mcp ai-review-changes \
    before-ai-coding after-ai-coding restart-services format lint clean-code dev-up dev-down \
    lambda-setup lambda-status lambda-ssh lambda-destroy lambda-provision

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

Lambda Labs-deploy:
	$(PYTHON) scripts/Lambda Labs_provision.py $(ARGS)

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

dev-up:
	cd infra/dev && pulumi up --yes | cat

dev-down:
	cd infra/dev && pulumi destroy --yes | cat

# Lambda Labs targets
lambda-setup:
	@echo "🚀 Running Lambda Labs setup..."
	@./lambda_quick_setup.sh

lambda-status:
	@echo "📊 Checking Lambda Labs instances..."
	@if [ -z "$$LAMBDA_TOKEN" ]; then \
		echo "Error: LAMBDA_TOKEN environment variable not set"; \
		exit 1; \
	fi; \
	curl -s -X GET -H "Authorization: Bearer $$LAMBDA_TOKEN" https://cloud.lambdalabs.com/api/v1/instances | jq '.data[] | {name, id, ip, status}'

lambda-ssh:
	@echo "🔗 Connecting to Lambda Labs VPS..."
	@ssh orchestra-dev

lambda-destroy:
	@echo "🔻 Destroying Lambda Labs VPS..."
	@if [ -f lambda_instance_info.json ]; then \
		./lambda_destroy.sh; \
	else \
		echo "No instance info found. Run 'make lambda-status' to check existing instances."; \
	fi

lambda-provision:
	@echo "🏗️ Provisioning Lambda Labs infrastructure with Pulumi..."
	@if [ -z "$$LAMBDA_TOKEN" ] || [ -z "$$GITHUB_PAT" ] || [ -z "$$SSH_KEY_ID" ]; then \
		echo "Error: Required environment variables not set (LAMBDA_TOKEN, GITHUB_PAT, SSH_KEY_ID)"; \
		exit 1; \
	fi; \
	pulumi stack select orchestra-dev || pulumi stack init orchestra-dev; \
	pulumi config set lambda:api_key "$$LAMBDA_TOKEN" --secret; \
	pulumi config set lambda:ssh_key_id "$$SSH_KEY_ID"; \
	pulumi config set github:token "$$GITHUB_PAT" --secret; \
	pulumi up --yes
