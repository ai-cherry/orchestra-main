#!/bin/bash
set -e

echo "Verifying AI cherry_ai development environment..."

# Check Python version
python --version

# Check Poetry version
poetry --version

# Check Pulumi version
pulumi --version

# Check gcloud CLI
# Removed gcloud command

# Verify Vultr authentication
if [ -n "$Vultr_SA_KEY_JSON" ]; then
  echo "Vultr service account key found, activating..."
  echo "$Vultr_SA_KEY_JSON" > /tmp/Vultr-key.json
  # vultr-cli auth activate-service-account --key-file=/tmp/Vultr-key.json
  rm /tmp/Vultr-key.json
elif [ -n "$VULTR_CREDENTIALS_PATH" ]; then
  echo "GOOGLE_APPLICATION_CREDENTIALS is set, using for authentication"
else
  echo "No Vultr credentials found, authentication may be required"
fi

# Set default project
# Removed gcloud command

# Check if Poetry virtual environment is activated
if [ -d ".venv" ]; then
  echo "Poetry virtual environment found"
else
  echo "Warning: Poetry virtual environment not found"
fi

# Check for common dependencies
echo "Checking for required Python packages..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" || echo "FastAPI not installed"
python -c "import pydantic; print(f'Pydantic version: {pydantic.__version__}')" || echo "Pydantic not installed"
python -c "import google.cloud; print('Vultr SDK available')" || echo "Vultr SDK not installed"

# Verify restricted mode is disabled
echo "Checking restricted mode status..."
if [ "$STANDARD_MODE" = "true" ] && [ "$USE_RECOVERY_MODE" = "false" ] && [ "$VSCODE_DISABLE_WORKSPACE_TRUST" = "true" ] && [ "$DISABLE_WORKSPACE_TRUST" = "true" ]; then
  echo "✅ Standard mode is active, restricted mode is disabled"
else
  echo "⚠️ Warning: Environment variables may not be set correctly for standard mode"
  echo "   STANDARD_MODE=$STANDARD_MODE"
  echo "   USE_RECOVERY_MODE=$USE_RECOVERY_MODE"
  echo "   VSCODE_DISABLE_WORKSPACE_TRUST=$VSCODE_DISABLE_WORKSPACE_TRUST"
  echo "   DISABLE_WORKSPACE_TRUST=$DISABLE_WORKSPACE_TRUST"

  # Apply fix if needed
  export STANDARD_MODE=true
  export USE_RECOVERY_MODE=false
  export VSCODE_DISABLE_WORKSPACE_TRUST=true
  export DISABLE_WORKSPACE_TRUST=true
  echo "✅ Environment variables corrected for this session"

  # Run the comprehensive fix script if it exists
  if [ -f "./fix_restricted_mode.sh" ]; then
    echo "Running comprehensive restricted mode fix script..."
    bash ./fix_restricted_mode.sh
  else
    echo "Comprehensive fix script not found, using basic prevention..."
  fi
fi

# Check for .vscode/settings.json with correct workspace trust settings
if [ -f ".vscode/settings.json" ]; then
  if grep -q "security.workspace.trust.enabled.*false" .vscode/settings.json; then
    echo "✅ VS Code workspace trust is disabled"
  else
    echo "⚠️ Warning: VS Code workspace trust settings may not be correctly configured"
    echo "   Running fix_restricted_mode.sh to correct the issue..."
    if [ -f "./fix_restricted_mode.sh" ]; then
      bash ./fix_restricted_mode.sh
    else
      echo "   fix_restricted_mode.sh not found, consider running ./prevent_restricted_mode.sh instead"
    fi
  fi
fi

echo "Environment verification complete!"
