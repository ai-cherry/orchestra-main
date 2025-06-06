#!/bin/bash

echo "Python Syntax Error Fixer"
echo "========================="
echo "This will fix all 644 Python files with indentation errors"
echo ""

# Check if we have the audit report
AUDIT_REPORT="audit_results_20250605/code_audit_report_20250605_004043.json"

if [ ! -f "$AUDIT_REPORT" ]; then
    echo "Error: Audit report not found at $AUDIT_REPORT"
    exit 1
fi

# Create backup directory with timestamp
BACKUP_DIR="syntax_fix_backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backup directory: $BACKUP_DIR"
echo ""

# Prompt for confirmation
read -p "This will modify 644 Python files. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting syntax fixes..."
echo "========================"

# Run the automated syntax fixer
python3 automated_syntax_fixer.py --audit-report "$AUDIT_REPORT"

# Check if report was generated
LATEST_REPORT=$(ls -t syntax_fix_report_*.json 2>/dev/null | head -1)

if [ -n "$LATEST_REPORT" ]; then
    echo ""
    echo "Fix Summary:"
    echo "============"
    
    # Extract and display summary
    python3 -c "
import json

with open('$LATEST_REPORT', 'r') as f:
    report = json.load(f)
    
stats = report['statistics']
print(f'Total files processed: {stats[\"total_files\"]}')
print(f'Successfully fixed: {stats[\"fixed\"]}')
print(f'Failed to fix: {stats[\"failed\"]}')
print(f'Already valid: {stats[\"already_valid\"]}')

if stats['fixed'] > 0:
    print(f'\n✓ Fixed {stats[\"fixed\"]} files!')
    
if stats['failed'] > 0:
    print(f'\n⚠️  {stats[\"failed\"]} files could not be fixed automatically')
    print('These may require manual intervention.')
"
    
    echo ""
    echo "Next steps:"
    echo "1. Test the fixed files: ./test_python_syntax.sh"
    echo "2. If tests pass, restart services: ./restart_services.sh"
    echo "3. Run security scan: ./security_scan.sh"
    
else
    echo "Error: Fix report not generated"
    exit 1
fi