#!/bin/bash
# This script sets appropriate execute permissions for all key scripts in the repository

echo "Setting execute permissions on key scripts..."

# Shell scripts
find . -name "*.sh" -not -path "*/\.*" -not -path "*/google-cloud-sdk/*" -type f -exec chmod +x {} \;
echo "✓ Set permissions on shell scripts"

# Python scripts that should be executable
KEY_PYTHON_SCRIPTS=(
  "unified_diagnostics.py"
  "scripts/setup_postgres_pgvector.py"
  "verify_deployment_readiness.py"
  "diagnose_environment.py"
  "diagnose_orchestrator.py"
)

# Set permissions for each key Python script
for script in "${KEY_PYTHON_SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    chmod +x "$script"
    echo "✓ Set execute permission on $script"
  else
    echo "⚠ Warning: $script not found"
  fi
done

# Main deployment and setup scripts that must be executable
KEY_SCRIPTS=(
  "setup_credentials.sh"
  "unified_setup.sh"
  "run_pre_deployment_automated.sh"
  "deploy_to_production.sh"
  "run_connection_tests.sh"
)

# Set permissions for each key script
for script in "${KEY_SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    chmod +x "$script"
    echo "✓ Verified execute permission on $script"
  else
    echo "⚠ Warning: $script not found"
  fi
done

echo ""
echo "Completed setting execute permissions."
echo "To make all shell scripts and key Python files executable in the future, run:"
echo "  ./make_scripts_executable.sh"
