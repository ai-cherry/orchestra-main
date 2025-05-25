#!/usr/bin/env bash
# validate_python_env.sh
# Enforces Python 3.10+ for all environments (local, CI, Docker).
# Fails early if requirements are not met.

set -e

REQUIRED_PYTHON="3.10"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || { [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 10 ]]; }; then
  echo "ERROR: Python 3.10+ is required. Detected: $PYTHON_VERSION"
  exit 1
fi

echo "✔ Python $PYTHON_VERSION meets requirements."
exit 0
