#!/bin/bash
# Auto-fix JavaScript/TypeScript formatting issues

echo "🔧 Fixing JavaScript/TypeScript formatting..."

# Check if prettier is installed
if ! command -v prettier &> /dev/null; then
    echo "Prettier not found. Install with: npm install -g prettier"
    exit 1
fi

# Fix files passed as arguments
if [ $# -eq 0 ]; then
    echo "Usage: ./fix_javascript_formatting.sh <file1> <file2> ..."
    exit 1
fi

for file in "$@"; do
    echo "Fixing: $file"
    prettier --write --print-width 120 --tab-width 2 "$file"
done

echo "✅ JavaScript/TypeScript formatting complete!"
