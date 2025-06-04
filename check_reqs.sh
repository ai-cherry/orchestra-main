#!/bin/bash
# check_reqs.sh: Find unused and missing requirements
set -e
source ~/cherry_ai-main/venv/bin/activate

# Install pip-check-reqs if not already installed
if ! pip show pip-check-reqs > /dev/null 2>&1; then
  echo "pip-check-reqs not found. Installing..."
  pip install pip-check-reqs
fi

echo "Checking for unused requirements (in requirements.txt but not imported)..."
pip-check-reqs --unused .

echo
echo "Checking for missing requirements (imported but not in requirements.txt)..."
pip-check-reqs --missing .
