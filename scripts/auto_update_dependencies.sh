#!/bin/bash
# Automated dependency updates with safety checks

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Configuration
MAX_RISK=${MAX_RISK:-5}
STRATEGY=${STRATEGY:-minor}
DRY_RUN=${DRY_RUN:-false}

# Activate virtual environment
source venv/bin/activate

echo "🔄 Automated Dependency Update"
echo "Strategy: $STRATEGY"
echo "Max Risk: $MAX_RISK"
echo "Dry Run: $DRY_RUN"
echo "=============================="

# Create backup
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup..."
cp -r requirements "$BACKUP_DIR/" 2>/dev/null || true
cp -r admin-ui/package*.json "$BACKUP_DIR/" 2>/dev/null || true
find . -name "Dockerfile*" -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true

# Run update
if [ "$DRY_RUN" = "true" ]; then
    python scripts/version_updater.py update --strategy "$STRATEGY" --max-risk "$MAX_RISK" --dry-run
else
    python scripts/version_updater.py update --strategy "$STRATEGY" --max-risk "$MAX_RISK" --output update-report.json
    
    # Check if updates were successful
    if [ -f "update-report.json" ]; then
        SUCCESS=$(python -c "import json; d=json.load(open('update-report.json')); print(d['summary']['successful'])")
        FAILED=$(python -c "import json; d=json.load(open('update-report.json')); print(d['summary']['failed'])")
        
        echo ""
        echo "Update Summary:"
        echo "  Successful: $SUCCESS"
        echo "  Failed: $FAILED"
        
        if [ "$FAILED" -gt 0 ]; then
            echo "⚠️  Some updates failed. Check update-report.json for details."
        fi
    fi
fi

echo ""
echo "✅ Update process completed"
echo "Backup saved to: $BACKUP_DIR"
