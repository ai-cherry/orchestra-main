#!/bin/bash
# pre-commit-batch-analysis.sh - Pre-commit hook to run batch code analysis using GCP services

set -eo pipefail

echo "Running batch code analysis pre-commit hook..."

# Check if the batch_code_analysis.sh script exists
if [ ! -f "scripts/batch_code_analysis.sh" ]; then
  echo "Error: batch_code_analysis.sh not found in scripts/ directory"
  exit 1
fi

# Execute the batch code analysis script
# You can customize the parameters (project ID, bucket name, function name) as needed
bash scripts/batch_code_analysis.sh

if [ $? -ne 0 ]; then
  echo "Batch code analysis failed. Please check the output for details."
  echo "To bypass this check temporarily, use 'git commit --no-verify'"
  exit 1
fi

echo "Batch code analysis completed successfully. Proceeding with commit."
exit 0