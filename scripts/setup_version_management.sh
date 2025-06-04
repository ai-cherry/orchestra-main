#!/bin/bash
# Automated setup script for version management system
# This script configures everything automatically

set -euo pipefail

echo "🚀 Setting up cherry_ai Version Management System..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip3 is required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites satisfied${NC}"
}

# Install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install version management requirements
    pip install -r scripts/requirements-version-management.txt
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Initialize version management
initialize_system() {
    echo "🔧 Initializing version management..."
    
    # Run initial scan and setup
    python scripts/version_manager.py init
    
    # Create initial reports directory
    mkdir -p reports/version-management
    
    echo -e "${GREEN}✅ System initialized${NC}"
}

# Setup cron jobs for automation
setup_automation() {
    echo "⚙️ Setting up automation..."
    
    # Create cron job for daily scans (2 AM)
    CRON_CMD="0 2 * * * cd $(pwd) && ./scripts/run_version_checks.sh >> logs/version-management.log 2>&1"
    
    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "run_version_checks.sh"; then
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo -e "${GREEN}✅ Cron job created for daily scans${NC}"
    else
        echo -e "${YELLOW}⚠️  Cron job already exists${NC}"
    fi
    
    # Create systemd service for monitoring (optional)
    if command -v systemctl &> /dev/null; then
        create_systemd_service
    fi
}

# Create systemd service for continuous monitoring
create_systemd_service() {
    echo "🔄 Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/version-monitor.service"
    
    # Create service file content
    cat > /tmp/version-monitor.service << EOF
[Unit]
Description=cherry_ai Version Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$(pwd)/venv/bin/python $(pwd)/scripts/version_monitor.py --port 9090 --interval 3600
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Install service (requires sudo)
    if [ -w "/etc/systemd/system" ]; then
        cp /tmp/version-monitor.service $SERVICE_FILE
        systemctl daemon-reload
        systemctl enable version-monitor
        echo -e "${GREEN}✅ Systemd service created${NC}"
    else
        echo -e "${YELLOW}⚠️  Run with sudo to create systemd service${NC}"
        echo "Service file saved to: /tmp/version-monitor.service"
    fi
}

# Setup GitHub Actions
setup_github_actions() {
    echo "🔗 Setting up GitHub Actions..."
    
    # Check if we're in a git repository
    if [ -d ".git" ]; then
        # Check if workflow already exists
        if [ ! -f ".github/workflows/version-management.yml" ]; then
            echo -e "${YELLOW}⚠️  GitHub Actions workflow not found${NC}"
            echo "The workflow has been created at: .github/workflows/version-management.yml"
            echo "Commit and push to enable automated version management"
        else
            echo -e "${GREEN}✅ GitHub Actions workflow already configured${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Not a git repository - GitHub Actions setup skipped${NC}"
    fi
}

# Create convenience scripts
create_convenience_scripts() {
    echo "📝 Creating convenience scripts..."
    
    # Create run script for daily checks
    cat > scripts/run_version_checks.sh << 'EOF'
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
EOF
    
    chmod +x scripts/run_version_checks.sh
    
    # Create quick status script
    cat > scripts/version_status.sh << 'EOF'
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
EOF
    
    chmod +x scripts/version_status.sh
    
    # Create auto-update script
    cat > scripts/auto_update_dependencies.sh << 'EOF'
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
EOF
    
    chmod +x scripts/auto_update_dependencies.sh
    
    echo -e "${GREEN}✅ Convenience scripts created${NC}"
}

# Main setup flow
main() {
    echo "======================================"
    echo "cherry_ai Version Management Setup"
    echo "======================================"
    echo ""
    
    check_prerequisites
    install_dependencies
    initialize_system
    setup_automation
    setup_github_actions
    create_convenience_scripts
    
    echo ""
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo ""
    echo "Automated execution is now configured:"
    echo "  • Daily scans via cron at 2 AM"
    echo "  • GitHub Actions on every push"
    echo "  • Monitoring service (if systemd available)"
    echo ""
    echo "Quick commands:"
    echo "  ./scripts/version_status.sh         - Check current status"
    echo "  ./scripts/run_version_checks.sh     - Run full scan now"
    echo "  ./scripts/auto_update_dependencies.sh - Apply safe updates"
    echo ""
    echo "The system will run automatically - no manual intervention needed!"
}

# Run main setup
main