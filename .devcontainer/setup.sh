#!/bin/bash
set -e

echo "Setting up AI Orchestra development environment..."

# Ensure Poetry is properly configured
poetry config virtualenvs.in-project true

# Check if poetry.lock exists and is up-to-date
if [ ! -f "poetry.lock" ] || [ "pyproject.toml" -nt "poetry.lock" ]; then
  echo "Generating poetry.lock file..."
  poetry lock --no-update
fi

# Install dependencies with retry mechanism
MAX_RETRIES=3
RETRY_COUNT=0
SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
  echo "Installing dependencies (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)..."
  if poetry install --with dev; then
    SUCCESS=true
  else
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      echo "Retrying in 5 seconds..."
      sleep 5
    fi
  fi
done

if [ "$SUCCESS" = false ]; then
  echo "Failed to install dependencies after $MAX_RETRIES attempts."
  exit 1
fi

# Create standard mode marker file
touch .standard_mode

# Install pre-commit hooks if config exists
if [ -f ".pre-commit-config.yaml" ]; then
  echo "Installing pre-commit hooks..."
  pre-commit install
fi

# Display environment information
echo "Environment setup complete!"
echo "Python version: $(python --version)"
echo "Poetry version: $(poetry --version)"

# Create GCP credentials directory if it doesn't exist
mkdir -p ~/.config/gcloud

# Prevent VS Code restricted mode
echo "Preventing VS Code restricted mode..."
# Set critical environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true

# Make all scripts executable
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null

# Run the comprehensive fix script if it exists
if [ -f "./fix_restricted_mode.sh" ]; then
  echo "Running comprehensive restricted mode fix script..."
  bash ./fix_restricted_mode.sh
else
  echo "Comprehensive fix script not found, using basic prevention..."
  
  # Update VS Code settings
  mkdir -p .vscode
  if [ -f .vscode/settings.json ]; then
    # Ensure workspace trust settings are correct
    sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' .vscode/settings.json 2>/dev/null
    sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' .vscode/settings.json 2>/dev/null
    sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' .vscode/settings.json 2>/dev/null
    sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' .vscode/settings.json 2>/dev/null
    echo "VS Code settings updated to prevent restricted mode"
  fi
fi

echo "Restricted mode prevention complete"

# Create a marker file to indicate setup has completed
touch .setup_complete
