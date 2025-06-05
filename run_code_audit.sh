#!/bin/bash
# Quick-start script for code quality audit

echo "🔍 Code Quality Audit Tool"
echo "========================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Make scripts executable
chmod +x code_audit_scanner.py
chmod +x code_audit_processor.py

# Step 1: Run the scanner
echo "📊 Step 1: Running code audit scanner..."
echo "This will analyze your codebase for:"
echo "  - Syntax errors"
echo "  - Formatting issues"
echo "  - Naming convention violations"
echo "  - Indentation problems"
echo ""

python3 code_audit_scanner.py

# Check if audit report was created
AUDIT_REPORT=$(ls -t code_audit_report_*.json 2>/dev/null | head -1)

if [ -z "$AUDIT_REPORT" ]; then
    echo "❌ Error: No audit report found. Scanner may have failed."
    exit 1
fi

echo ""
echo "✅ Audit complete! Report saved to: $AUDIT_REPORT"
echo ""

# Step 2: Process the results
echo "📋 Step 2: Processing audit results..."
python3 code_audit_processor.py "$AUDIT_REPORT"

# Check if fix plan was created
FIX_PLAN=$(ls -t code_fix_plan_*.json 2>/dev/null | head -1)

if [ -z "$FIX_PLAN" ]; then
    echo "❌ Error: No fix plan found. Processor may have failed."
    exit 1
fi

echo ""
echo "✅ Fix plan created: $FIX_PLAN"
echo ""

# Show next steps
echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "1. Review the audit report: $AUDIT_REPORT"
echo "   - Check 'syntax_errors' section for critical issues"
echo "   - Review 'formatting_issues' for style problems"
echo ""
echo "2. Review the fix plan: $FIX_PLAN"
echo "   - Check 'priority_fixes' for critical items"
echo "   - Review 'batch_fixes' for automated solutions"
echo ""
echo "3. For automated fixes, run:"
echo "   python3 batch_fix_runner.py $FIX_PLAN"
echo ""
echo "4. For manual syntax error fixes:"
echo "   - Open files listed in syntax_errors"
echo "   - Fix issues based on error messages"
echo "   - Test each fix before moving to next file"
echo ""
echo "💡 Tip: Start with syntax errors in core modules first!"