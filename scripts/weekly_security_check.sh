#!/bin/bash
# Weekly Security Check for Orchestra AI
# Run this with cron: 0 2 * * 1 /root/orchestra-main/scripts/weekly_security_check.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/security"
REPORT_DIR="$PROJECT_ROOT/reports/security"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/security_check_$DATE.log"

# Create directories if they don't exist
mkdir -p "$LOG_DIR" "$REPORT_DIR"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Header function
print_header() {
    log "\n${BLUE}===============================================${NC}"
    log "${BLUE}$1${NC}"
    log "${BLUE}===============================================${NC}\n"
}

# Start security check
print_header "Weekly Security Check - $(date)"

# Change to project directory
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    log "Activating virtual environment..."
    source venv/bin/activate
fi

# Update security tools
print_header "Updating Security Tools"
log "Updating pip-audit and safety..."
pip install --upgrade pip-audit safety >> "$LOG_FILE" 2>&1

# Run Python security audit script
print_header "Running Comprehensive Security Audit"
if python scripts/security_audit.py; then
    log "${GREEN}✓ Security audit completed successfully${NC}"
else
    log "${RED}✗ Security audit found vulnerabilities${NC}"
fi

# Check for outdated packages
print_header "Checking for Outdated Packages"
log "Running pip list --outdated..."
pip list --outdated > "$REPORT_DIR/outdated_packages_$DATE.txt"
OUTDATED_COUNT=$(wc -l < "$REPORT_DIR/outdated_packages_$DATE.txt")
log "Found $OUTDATED_COUNT outdated packages"

# Check GitHub Dependabot alerts (requires gh CLI)
if command -v gh &> /dev/null; then
    print_header "Checking GitHub Dependabot Alerts"
    gh api repos/ai-cherry/orchestra-main/vulnerability-alerts \
        --jq '.[] | {package: .affected_package_name, severity: .severity}' \
        > "$REPORT_DIR/github_alerts_$DATE.json" 2>/dev/null || \
        log "${YELLOW}⚠ Could not fetch GitHub alerts (may need authentication)${NC}"
fi

# Run license check
print_header "Checking License Compliance"
pip-licenses --format=json > "$REPORT_DIR/licenses_$DATE.json"
log "License report generated"

# Generate summary report
print_header "Generating Summary Report"
SUMMARY_FILE="$REPORT_DIR/weekly_summary_$DATE.md"

cat > "$SUMMARY_FILE" << EOF
# Weekly Security Report
Generated: $(date)

## Security Scan Results
$(tail -n 20 "$LOG_FILE" | grep -E "(vulnerabilities|secure|error)" || echo "See detailed logs")

## Outdated Packages
Total: $OUTDATED_COUNT packages need updates

## Recommendations
1. Review and update vulnerable packages immediately
2. Plan updates for outdated packages
3. Check detailed reports in: $REPORT_DIR

## Next Steps
- Enable GitHub Dependabot if not already enabled
- Review security audit report: security_audit_report_*.json
- Update packages using: pip install --upgrade <package>
EOF

log "\n${GREEN}Summary report saved to: $SUMMARY_FILE${NC}"

# Send notification (optional - configure as needed)
# Example: Send email notification
# mail -s "Weekly Security Report - Orchestra AI" admin@example.com < "$SUMMARY_FILE"

# Cleanup old logs (keep last 4 weeks)
print_header "Cleaning Up Old Logs"
find "$LOG_DIR" -name "security_check_*.log" -mtime +28 -delete
find "$REPORT_DIR" -name "*" -mtime +28 -delete
log "Old logs cleaned up"

log "\n${GREEN}Weekly security check completed!${NC}"
log "Full log available at: $LOG_FILE"
log "Reports available in: $REPORT_DIR"

# Exit with appropriate code
if grep -q "vulnerabilities" "$LOG_FILE"; then
    exit 1
else
    exit 0
fi 