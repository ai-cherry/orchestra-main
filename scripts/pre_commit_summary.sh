#!/bin/bash

echo "🚀 Pre-commit Status Summary"
echo "============================"
echo ""

# Run pre-commit and capture output
echo "Running pre-commit hooks..."
pre_commit_output=$(pre-commit run --all-files 2>&1)

# Check each hook
echo "📊 Hook Status:"
echo "--------------"
echo "$pre_commit_output" | grep -E "(black|mypy|flake8|check yaml|fix end of files|trim trailing whitespace|Validate Python).*\.(Passed|Failed)" | while read line; do
    if [[ $line == *"Passed"* ]]; then
        echo "✅ $line"
    else
        echo "❌ $line"
    fi
done

echo ""
echo "📋 Issue Summary:"
echo "----------------"

# Count flake8 issues
flake8_count=$(pre-commit run flake8 --all-files 2>&1 | grep -E "F401|F541|F841|W605|F821" | wc -l)
echo "Flake8 issues: $flake8_count"

# Count mypy errors
mypy_errors=$(pre-commit run mypy --all-files 2>&1 | grep -c "error:")
echo "Mypy errors: $mypy_errors"

echo ""
echo "🔧 Quick Fixes:"
echo "--------------"
echo "1. Run: python scripts/fix_pre_commit_issues.py"
echo "2. Fix remaining type annotations manually"
echo "3. Run: pre-commit run --all-files"
