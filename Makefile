PYTHON?=python3

.PHONY: dev-start validate service-status start-services stop-services \
    health-check health-monitor wait-for-mcp ai-review-changes \
    before-ai-coding after-ai-coding restart-services

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
