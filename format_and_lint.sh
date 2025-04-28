#!/bin/bash
# format_and_lint.sh - Script to run formatting and linting across the codebase
# Usage: ./format_and_lint.sh [--check] [--fix]

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

# Set up pre-commit hooks if not already installed
echo "Ensuring pre-commit hooks are installed..."
pre-commit install

# Check or fix the formatting
if [ "$CHECK_ONLY" = true ]; then
    echo ""
    echo "===== Checking code formatting (no changes will be made) ====="
    
    echo "\n> Running black (check only)..."
    python -m black --check .
    
    echo "\n> Running isort (check only)..."
    python -m isort --check-only --profile black .
    
    echo "\n> Running ruff linter (check only)..."
    python -m ruff check .
    
    echo "\n===== If any issues were found, run with --fix to correct them ====="
elif [ "$FIX" = true ]; then
    echo ""
    echo "===== Fixing code formatting ====="
    
    echo "\n> Running black..."
    python -m black .
    
    echo "\n> Running isort..."
    python -m isort --profile black .
    
    echo "\n> Running ruff linter with auto-fix..."
    python -m ruff check --fix .
    
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
