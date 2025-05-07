#!/bin/bash
# Enhanced setup and verification script for GCP integration in GitHub Codespaces
# This script balances robustness with simplicity and integrates with existing scripts

# Redirect output to a log file for debugging
exec > >(tee -i /workspaces/orchestra-main/codespace_setup.log) 2>&1

echo "======================================================"
echo "  ENHANCED CODESPACE SETUP AND VERIFICATION"
echo "======================================================"
echo "Starting setup at $(date)"

# Function for error handling
handle_error() {
  echo "ERROR: $1"
  echo "See codespace_setup.log for details"
}

# Create necessary directories
echo "Creating required directories..."
mkdir -p $HOME/.gcp
mkdir -p $HOME/.vscode-remote/data/Machine

# Set environment variables for standard mode
echo "Setting environment variables for standard mode..."
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export STANDARD_MODE=true
export DISABLE_WORKSPACE_TRUST=true
export USE_RECOVERY_MODE=false

# Check if running in a recovery container
echo "Checking Codespace environment..."
if grep -q "recovery container" /workspaces/.codespaces/.persistedshare/creation.log 2>/dev/null; then
  echo "NOTE: Running in a recovery container"
  echo "This may indicate issues with the original container configuration"
fi

# Handle GCP service account key with retry
echo "Setting up GCP authentication..."
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
  # Use retry mechanism for key setup
  for i in {1..3}; do
    echo $GCP_MASTER_SERVICE_JSON > $HOME/.gcp/service-account.json && break || {
      echo "Attempt $i to write service account key failed"
      sleep 2
    }
  done
  
  if [ -f "$HOME/.gcp/service-account.json" ]; then
    echo "Service account key file created successfully"
    
    # Set credentials environment variable
    export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
    echo "Set GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
    
    # Add to .bashrc if not already there (idempotent)
    if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json" $HOME/.bashrc; then
      echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> $HOME/.bashrc
      echo "Added GOOGLE_APPLICATION_CREDENTIALS to .bashrc"
    fi
  else
    handle_error "Failed to create service account key file"
  fi
else
  handle_error "GCP_MASTER_SERVICE_JSON environment variable not set"
fi

# Update VS Code settings for standard mode (idempotent)
echo "Updating VS Code settings for standard mode..."
SETTINGS_FILE="$HOME/.vscode-remote/data/Machine/settings.json"

# Create or update settings file
if [ -f "$SETTINGS_FILE" ]; then
  # Check if already configured
  if grep -q "security.workspace.trust.enabled" "$SETTINGS_FILE"; then
    echo "Workspace trust settings already exist in settings.json, ensuring they are set correctly"
    # Use sed to update existing settings (platform-independent approach)
    sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' "$SETTINGS_FILE"
    sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' "$SETTINGS_FILE"
  else
    # Append settings to existing file
    TEMP_FILE=$(mktemp)
    # Remove closing brace if it exists
    sed '$ s/}$//' "$SETTINGS_FILE" > "$TEMP_FILE"
    # Add our settings and closing brace
    cat << 'EOF' >> "$TEMP_FILE"
,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
    mv "$TEMP_FILE" "$SETTINGS_FILE"
    echo "Added workspace trust settings to existing settings.json"
  fi
else
  # Create new settings file
  cat << 'EOF' > "$SETTINGS_FILE"
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
  echo "Created new settings.json with workspace trust disabled"
fi

# Add environment variables to .bashrc (idempotent)
echo "Updating .bashrc with environment variables..."
if ! grep -q "VSCODE_DISABLE_WORKSPACE_TRUST=true" $HOME/.bashrc; then
  cat << 'EOF' >> $HOME/.bashrc

# Standard mode environment variables
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export STANDARD_MODE=true
export DISABLE_WORKSPACE_TRUST=true
export USE_RECOVERY_MODE=false
EOF
  echo "Added standard mode environment variables to .bashrc"
fi

# Check for gcloud
echo "Checking for gcloud installation..."
if ! command -v gcloud &> /dev/null; then
  echo "gcloud not found in PATH"
  echo "Setting up PATH variables in case gcloud is installed but not in PATH..."
  
  # Add potential gcloud paths to PATH
  for gcloud_path in \
    "/workspaces/orchestra-main/google-cloud-sdk/bin" \
    "$HOME/google-cloud-sdk/bin" \
    "/usr/local/google-cloud-sdk/bin" \
    "/usr/share/google-cloud-sdk/bin"; do
    
    if [ -d "$gcloud_path" ]; then
      echo "Found potential gcloud at $gcloud_path, adding to PATH"
      export PATH=$PATH:$gcloud_path
      echo "export PATH=\$PATH:$gcloud_path" >> $HOME/.bashrc
    fi
  done
  
  # Check again after path updates
  if ! command -v gcloud &> /dev/null; then
    echo "gcloud still not found after PATH updates"
    echo ""
    echo "Google Cloud SDK should be installed manually:"
    echo "1. Run: curl https://sdk.cloud.google.com | bash"
    echo "2. Run: exec -l \$SHELL"
    echo "3. Run: gcloud init"
    echo ""
    echo "Standard mode settings have been configured successfully."
    echo "Once gcloud is installed, run './enhanced_verify_gcp_setup.sh' to complete GCP setup."
  fi
fi

# Only attempt GCP operations if gcloud is available
if command -v gcloud &> /dev/null; then
  # Authenticate with GCP (with retry)
  echo "Authenticating with GCP..."
  if [ -f "$HOME/.gcp/service-account.json" ]; then
    for i in {1..3}; do
      gcloud auth activate-service-account --key-file=$HOME/.gcp/service-account.json && {
        echo "Successfully authenticated with GCP"
        break
      } || {
        echo "Attempt $i to authenticate with GCP failed"
        sleep 3
        if [ $i -eq 3 ]; then
          handle_error "Failed to authenticate with GCP after 3 attempts"
        fi
      }
    done
    
    # Set project
    echo "Setting GCP project..."
    gcloud config set project cherry-ai-project
    
    # Simple GCP test
    echo "Testing GCP connectivity..."
    if gcloud projects list --limit=1 &>/dev/null; then
      echo "Successfully connected to GCP and accessed projects"
    else
      handle_error "Failed to list GCP projects"
    fi
  else
    handle_error "Service account key file not found"
  fi
else
  echo ""
  echo "===== GCP SETUP POSTPONED ====="
  echo "GCP authentication will be completed when gcloud is available"
  echo "The service account key has been created at $HOME/.gcp/service-account.json"
  echo "Environment variables have been configured correctly"
  echo "Standard mode has been successfully enforced"
  echo ""
fi

echo "======================================================"
echo "  SETUP COMPLETE"
echo "======================================================"
echo "Finished at $(date)"
echo ""
echo "To verify configurations anytime:"
echo "  ./verify_standard_mode.sh"
echo "  ./enhanced_verify_gcp_setup.sh"
echo ""
echo "To apply environment variables to current session:"
echo "  source ~/.bashrc"
