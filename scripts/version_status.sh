#!/bin/bash
# Quick version management status check

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Activate virtual environment
source venv/bin/activate

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 cherry_ai Version Management Status"
echo "====================================="

# Get latest report
LATEST_REPORT=$(find reports/version-management -name "summary.json" -type f 2>/dev/null | sort -r | head -1)

if [ -z "$LATEST_REPORT" ]; then
    echo -e "${YELLOW}No reports found. Run: ./scripts/run_version_checks.sh${NC}"
    exit 1
fi

# Display summary
python -c "
import json
from pathlib import Path
from datetime import datetime

with open('$LATEST_REPORT') as f:
    data = json.load(f)

print(f\"\\nLast check: {data['timestamp']}\")
print(f\"\\nSecurity:\")
print(f\"  Vulnerabilities: {data['security']['vulnerable_dependencies']}\")
print(f\"  Critical updates: {data['security']['critical_updates']}\")
print(f\"\\nUpdates:\")
print(f\"  Available: {data['updates']['available']}\")
print(f\"  Security: {data['updates']['security_updates']}\")
print(f\"\\nHealth: {data['health']['status']}\")
print(f\"Active alerts: {data['health']['active_alerts']}\")

if data['action_needed']:
    print(\"\\n⚠️  ACTION REQUIRED!\")
else:
    print(\"\\n✅ All systems healthy\")
"

echo -e "\n${GREEN}Run './scripts/run_version_checks.sh' for fresh scan${NC}"
