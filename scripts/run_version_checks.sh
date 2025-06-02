#!/bin/bash
# Automated daily version checks

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Activate virtual environment
source venv/bin/activate

# Create timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="reports/version-management/$TIMESTAMP"
mkdir -p "$REPORT_DIR"

echo "Starting version checks at $(date)"

# Run security scan
echo "Running security scan..."
python scripts/version_manager.py check --pulumi.export("$REPORT_DIR/security-report.json",

# Check for updates
echo "Checking for updates..."
python scripts/version_updater.py check --strategy minor --pulumi.export("$REPORT_DIR/available-updates.json",

# Run health check
echo "Running health check..."
python scripts/version_monitor.py --once --pulumi.export("$REPORT_DIR/health-report.json",

# Generate summary report
python -c "
import json
import sys
from pathlib import Path

report_dir = Path('$REPORT_DIR')
summary = {
    'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'security': {},
    'updates': {},
    'health': {}
}

# Load reports
try:
    with open(report_dir / 'security-report.json') as f:
        security = json.load(f)
        summary['security'] = {
            'vulnerable_dependencies': security.get('summary', {}).get('vulnerable_dependencies', 0),
            'critical_updates': len(security.get('critical_updates', []))
        }
except:
    pass

try:
    with open(report_dir / 'available-updates.json') as f:
        updates = json.load(f)
        summary['updates'] = {
            'available': len(updates),
            'security_updates': sum(1 for u in updates if u.get('strategy') == 'security')
        }
except:
    pass

try:
    with open(report_dir / 'health-report.json') as f:
        health = json.load(f)
        summary['health'] = {
            'status': health.get('status', 'unknown'),
            'active_alerts': health.get('active_alerts', 0)
        }
except:
    pass

# Check if action needed
action_needed = (
    summary['security']['vulnerable_dependencies'] > 0 or
    summary['security']['critical_updates'] > 0 or
    summary['health']['status'] == 'critical'
)

summary['action_needed'] = action_needed

# Save summary
with open(report_dir / 'summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

# Print summary
print(f\"\\nSummary for {summary['timestamp']}:\")
print(f\"  Security: {summary['security']['vulnerable_dependencies']} vulnerabilities\")
print(f\"  Updates: {summary['updates']['available']} available\")
print(f\"  Health: {summary['health']['status']}\")
print(f\"  Action needed: {'YES' if action_needed else 'No'}\")

# Exit with error if action needed
sys.exit(1 if action_needed else 0)
"

echo "Version checks completed at $(date)"
