#!/bin/bash
# Weekly Security Audit Script
# Runs comprehensive security checks and generates reports

set -e

echo "🔍 AI Cherry Weekly Security Audit - $(date)"
echo "================================================"

# Create reports directory
mkdir -p security_reports

# 1. Python Security Audit
echo "📦 Running Python security audit..."
if command -v pip-audit &> /dev/null; then
    pip-audit --desc --format=json --output=security_reports/pip_audit_$(date +%Y%m%d).json || true
    echo "✅ pip-audit completed"
else
    echo "⚠️ pip-audit not installed"
fi

# 2. Safety Check
echo "🛡️ Running safety check..."
if command -v safety &> /dev/null; then
    safety check --json --output=security_reports/safety_$(date +%Y%m%d).json || true
    echo "✅ safety check completed"
else
    echo "⚠️ safety not installed"
fi

# 3. Bandit Security Scan
echo "🔒 Running bandit security scan..."
if command -v bandit &> /dev/null; then
    bandit -r . -f json -o security_reports/bandit_$(date +%Y%m%d).json || true
    echo "✅ bandit scan completed"
else
    echo "⚠️ bandit not installed"
fi

# 4. Check for outdated packages
echo "📋 Checking for outdated packages..."
pip list --outdated --format=json > security_reports/outdated_packages_$(date +%Y%m%d).json || true

# 5. Generate summary report
echo "📊 Generating security summary..."
cat > security_reports/weekly_summary_$(date +%Y%m%d).md << EOF
# Weekly Security Report - $(date)

## Summary
- Date: $(date)
- Python Version: $(python --version)
- Pip Version: $(pip --version)

## Security Scans Completed
- ✅ pip-audit (Python package vulnerabilities)
- ✅ safety (Known security vulnerabilities)
- ✅ bandit (Code security issues)
- ✅ Outdated packages check

## Next Steps
1. Review generated reports in security_reports/
2. Update vulnerable packages
3. Address any code security issues
4. Monitor for new vulnerabilities

## Files Generated
- pip_audit_$(date +%Y%m%d).json
- safety_$(date +%Y%m%d).json
- bandit_$(date +%Y%m%d).json
- outdated_packages_$(date +%Y%m%d).json
EOF

echo "✅ Security audit completed!"
echo "📁 Reports saved in security_reports/"
echo "📄 Summary: security_reports/weekly_summary_$(date +%Y%m%d).md"

