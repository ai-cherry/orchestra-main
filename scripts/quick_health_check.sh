#!/bin/bash
# quick_health_check.sh - Quick health check for AI optimization framework

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/root/orchestra-main}"
LOG_FILE="$PROJECT_ROOT/logs/quick_health.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "$(date): Running quick health check..." | tee -a "$LOG_FILE"

# Check for temporary files
echo "Checking for temporary files..." | tee -a "$LOG_FILE"
TEMP_FILE_COUNT=$(find "$PROJECT_ROOT" -type f \( -name "tmp_*" -o -name "temp_*" -o -name "*.tmp" -o -name "*.bak" \) -not -path "*/venv/*" -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null | wc -l)
echo "  Found $TEMP_FILE_COUNT temporary files" | tee -a "$LOG_FILE"

if [ "$TEMP_FILE_COUNT" -gt 50 ]; then
    echo "  ⚠️  WARNING: High number of temporary files found: $TEMP_FILE_COUNT" | tee -a "$LOG_FILE"
fi

# Check for large Python files
echo "Checking for large Python files..." | tee -a "$LOG_FILE"
LARGE_FILES=$(find "$PROJECT_ROOT" -name "*.py" -size +700k -not -path "*/venv/*" -not -path "*/.git/*" 2>/dev/null | wc -l)
echo "  Found $LARGE_FILES large Python files (>700KB)" | tee -a "$LOG_FILE"

# Check cleanup registry
echo "Checking cleanup registry..." | tee -a "$LOG_FILE"
if [ -f "$PROJECT_ROOT/.cleanup_registry.json" ]; then
    REGISTRY_SIZE=$(wc -l < "$PROJECT_ROOT/.cleanup_registry.json")
    echo "  Cleanup registry has $REGISTRY_SIZE lines" | tee -a "$LOG_FILE"
else
    echo "  Cleanup registry not found (will be created when needed)" | tee -a "$LOG_FILE"
fi

# Check automation health files
echo "Checking automation health..." | tee -a "$LOG_FILE"
if [ -d "$PROJECT_ROOT/status/automation_health" ]; then
    HEALTH_FILES=$(find "$PROJECT_ROOT/status/automation_health" -name "*.health" -type f 2>/dev/null | wc -l)
    FAILED_SCRIPTS=$(find "$PROJECT_ROOT/status/automation_health" -name "*.health" -type f -exec grep -l "^failed" {} \; 2>/dev/null | wc -l)
    echo "  Found $HEALTH_FILES health files, $FAILED_SCRIPTS failed" | tee -a "$LOG_FILE"
    
    if [ "$FAILED_SCRIPTS" -gt 0 ]; then
        echo "  ⚠️  WARNING: $FAILED_SCRIPTS automation scripts reported failure" | tee -a "$LOG_FILE"
    fi
else
    echo "  No automation health directory found yet" | tee -a "$LOG_FILE"
fi

# Check for untracked Python files
echo "Checking for untracked Python files..." | tee -a "$LOG_FILE"
if command -v git >/dev/null 2>&1 && git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    UNTRACKED_PY=$(git -C "$PROJECT_ROOT" ls-files --others --exclude-standard | grep "\.py$" | wc -l)
    echo "  Found $UNTRACKED_PY untracked Python files" | tee -a "$LOG_FILE"
fi

# Summary
echo "" | tee -a "$LOG_FILE"
echo "=== Health Check Summary ===" | tee -a "$LOG_FILE"
echo "Temporary files: $TEMP_FILE_COUNT" | tee -a "$LOG_FILE"
echo "Large Python files: $LARGE_FILES" | tee -a "$LOG_FILE"
echo "Failed automation scripts: ${FAILED_SCRIPTS:-0}" | tee -a "$LOG_FILE"
echo "Untracked Python files: ${UNTRACKED_PY:-0}" | tee -a "$LOG_FILE"

# Exit with warning if issues found
if [ "$TEMP_FILE_COUNT" -gt 50 ] || [ "${FAILED_SCRIPTS:-0}" -gt 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "⚠️  Issues detected. Review log at: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"
echo "✅ Health check passed" | tee -a "$LOG_FILE"
echo "$(date): Quick health check complete." | tee -a "$LOG_FILE"