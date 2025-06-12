#!/bin/bash
echo "🔍 Running pre-commit quality checks..."
echo "🔍 Quick syntax check for pre-commit..."

# Basic Python syntax check for staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep "\.py$")

for file in $staged_files; do
    if [[ -f "$file" ]]; then
        python3 -m py_compile "$file" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "❌ Python syntax error in: $file"
            exit 1
        fi
    fi
done

# Basic JSON syntax check
staged_json=$(git diff --cached --name-only --diff-filter=ACM | grep "\.json$")
for file in $staged_json; do
    if [[ -f "$file" ]]; then
        python3 -m json.tool "$file" >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "❌ JSON syntax error in: $file"
            exit 1
        fi
    fi
done

echo "✅ All staged files pass syntax validation"
echo "✅ Pre-commit checks passed!" 