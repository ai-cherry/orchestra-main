#!/bin/bash

# Orchestra AI Development Helpers

# Activate virtual environment
alias activate-venv='source venv/bin/activate'

# API commands
alias run-api='python -m uvicorn orchestra_api.main:app --reload --host 0.0.0.0 --port 8000'
alias test-api='python -m pytest tests/api/'

# Admin UI commands
alias run-ui='cd admin-interface && npm start'
alias build-ui='cd admin-interface && npm run build'

# Utility commands
alias fix-format='black . && isort .'
alias check-types='mypy .'
alias run-tests='pytest'

# MCP commands
alias mcp-status='python scripts/check_mcp_servers.sh'
alias mcp-start='python scripts/start_mcp_system.sh'
alias mcp-stop='python scripts/stop_mcp_system.sh'

echo "✅ Development helpers loaded"
echo "Available commands: run-api, run-ui, run-tests, fix-format, etc."
