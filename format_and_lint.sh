#!/bin/bash
# format_and_lint.sh - Script to run formatting and linting across the codebase
# Usage: ./format_and_lint.sh [--check] [--fix]

set -e

# Set default behavior
CHECK_ONLY=false
FIX=false

# Process arguments
for arg in "$@"; do
  case $arg in
    --check)
      CHECK_ONLY=true
      ;;
    --fix)
      FIX=true
      ;;
  esac
done

echo "===== Orchestra Repository Code Quality Tool ====="
echo "Running code formatting and linting operations..."
echo ""

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Add pre-commit hooks
if [ -f .pre-commit-config.yaml ]; then
    pre-commit install
    echo "Pre-commit hooks installed."
else
    echo "No pre-commit configuration found. Skipping."
fi

# Check or fix the formatting
if [ "$CHECK_ONLY" = true ]; then
    echo ""
    echo "===== Checking code formatting (no changes will be made) ====="
    
    echo "\n> Running black (check only)..."
    python -m black --check .
    
    echo "\n> Running flake8 (check only)..."
    flake8 .
    
    echo "\n> Running pylint (check only)..."
    pylint $(find . -name "*.py")
    
    echo "\n===== If any issues were found, run with --fix to correct them ====="
elif [ "$FIX" = true ]; then
    echo ""
    echo "===== Fixing code formatting ====="
    
    echo "\n> Running black..."
    python -m black .
    
    echo "\n> Running flake8..."
    flake8 .
    
    echo "\n> Running pylint..."
    pylint $(find . -name "*.py")
    
    echo "\n===== Formatting fixes applied. Some issues may require manual fixes. ====="
else
    # Default: run pre-commit on all files
    echo ""
    echo "===== Running pre-commit on all files ====="
    pre-commit run --all-files
fi

echo ""
echo "===== Running additional linting checks ====="

# Check for unused imports and undefined names (critical issues)
echo "\n> Checking for unused imports and undefined names..."
python -m ruff check --select F401,F821 .

# Check for overly complex functions
echo "\n> Checking for overly complex functions..."
python -m ruff check --select C901 --show-source .

echo ""
echo "===== Code quality check complete ====="
