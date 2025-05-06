#!/bin/bash
# Comprehensive fix for VS Code Restricted Mode in GitHub Codespaces
# This script addresses all potential causes of restricted mode

set -e

echo "Applying comprehensive fix for VS Code restricted mode..."

# 1. Set critical environment variables in multiple locations for persistence
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true

# 2. Add to shell configuration files for persistence across sessions
for config_file in ~/.bashrc ~/.profile ~/.bash_profile ~/.zshrc; do
  if [ -f "$config_file" ]; then
    echo "Updating $config_file..."
    # Remove any existing mode settings to avoid duplication
    grep -v "USE_RECOVERY_MODE\|STANDARD_MODE\|VSCODE_DISABLE_WORKSPACE_TRUST\|DISABLE_WORKSPACE_TRUST" "$config_file" > "${config_file}.tmp" || true
    mv "${config_file}.tmp" "$config_file" || true
    
    # Add the environment variables
    cat << 'EOF' >> "$config_file"

# Orchestra mode control environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true
EOF
  fi
done

# 3. Update VS Code workspace settings
mkdir -p .vscode
if [ -f .vscode/settings.json ]; then
  echo "Updating workspace settings..."
  # Use more robust sed patterns with error suppression
  sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' .vscode/settings.json 2>/dev/null || true
  sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' .vscode/settings.json 2>/dev/null || true
  sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' .vscode/settings.json 2>/dev/null || true
  sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' .vscode/settings.json 2>/dev/null || true
  
  # Add settings if they don't exist (more comprehensive approach)
  if ! grep -q "security.workspace.trust.enabled" .vscode/settings.json; then
    # If the file doesn't end with a closing brace, add a comma, otherwise replace the closing brace
    sed -i 's/}$/,\n  "security.workspace.trust.enabled": false\n}/' .vscode/settings.json 2>/dev/null || true
  fi
  if ! grep -q "security.workspace.trust.startupPrompt" .vscode/settings.json; then
    sed -i 's/}$/,\n  "security.workspace.trust.startupPrompt": "never"\n}/' .vscode/settings.json 2>/dev/null || true
  fi
  if ! grep -q "security.workspace.trust.banner" .vscode/settings.json; then
    sed -i 's/}$/,\n  "security.workspace.trust.banner": "never"\n}/' .vscode/settings.json 2>/dev/null || true
  fi
  if ! grep -q "security.workspace.trust.emptyWindow" .vscode/settings.json; then
    sed -i 's/}$/,\n  "security.workspace.trust.emptyWindow": false\n}/' .vscode/settings.json 2>/dev/null || true
  fi
else
  # Create new settings.json with all required settings
  echo "Creating new workspace settings file..."
  cat << EOF > .vscode/settings.json
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false,
  "security.workspace.trust.untrustedFiles": "open",
  "editor.formatOnSave": true,
  "python.defaultInterpreterPath": "./.venv/bin/python"
}
EOF
fi

# 4. Update global VS Code settings (if in Codespace)
if [ -d "/home/codespace/.vscode-remote/data/Machine" ]; then
  echo "Updating global VS Code settings..."
  GLOBAL_SETTINGS="/home/codespace/.vscode-remote/data/Machine/settings.json"
  
  # Create or update global settings
  if [ -f "$GLOBAL_SETTINGS" ]; then
    # Update existing settings
    sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' "$GLOBAL_SETTINGS" 2>/dev/null || true
    sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' "$GLOBAL_SETTINGS" 2>/dev/null || true
    sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' "$GLOBAL_SETTINGS" 2>/dev/null || true
    sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' "$GLOBAL_SETTINGS" 2>/dev/null || true
    
    # Add settings if they don't exist
    if ! grep -q "security.workspace.trust.enabled" "$GLOBAL_SETTINGS"; then
      sed -i 's/}$/,\n  "security.workspace.trust.enabled": false\n}/' "$GLOBAL_SETTINGS" 2>/dev/null || true
    fi
  else
    # Create new global settings file
    mkdir -p "$(dirname "$GLOBAL_SETTINGS")"
    cat << EOF > "$GLOBAL_SETTINGS"
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false,
  "security.workspace.trust.untrustedFiles": "open"
}
EOF
  fi
fi

# 5. Create standard mode marker files
touch .standard_mode
touch .vscode/.standard_mode

# 6. Fix filesystem permissions
echo "Fixing filesystem permissions..."
# Make all scripts executable
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true

# 7. Create a startup hook to ensure settings are applied on each session
mkdir -p .devcontainer/startup
cat << 'EOF' > .devcontainer/startup/prevent_restricted.sh
#!/bin/bash
# This script runs on each terminal startup to ensure restricted mode is disabled

# Set critical environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true

# Check if VS Code settings are correct
if [ -f .vscode/settings.json ]; then
  if ! grep -q '"security.workspace.trust.enabled": false' .vscode/settings.json; then
    echo "⚠️ VS Code workspace trust settings need fixing. Running fix_restricted_mode.sh..."
    ./fix_restricted_mode.sh
  fi
fi

# Create standard mode marker file if it doesn't exist
if [ ! -f .standard_mode ]; then
  touch .standard_mode
fi
EOF

chmod +x .devcontainer/startup/prevent_restricted.sh

# 8. Add the startup hook to shell initialization
for config_file in ~/.bashrc ~/.profile ~/.bash_profile ~/.zshrc; do
  if [ -f "$config_file" ]; then
    if ! grep -q ".devcontainer/startup/prevent_restricted.sh" "$config_file"; then
      echo "Adding startup hook to $config_file..."
      echo "# Run restricted mode prevention on startup" >> "$config_file"
      echo "if [ -f \"\$PWD/.devcontainer/startup/prevent_restricted.sh\" ]; then" >> "$config_file"
      echo "  source \"\$PWD/.devcontainer/startup/prevent_restricted.sh\"" >> "$config_file"
      echo "fi" >> "$config_file"
    fi
  fi
done

# 9. Update devcontainer.json to ensure settings are applied
if [ -f .devcontainer/devcontainer.json ]; then
  echo "Ensuring devcontainer.json has correct settings..."
  # This is a simplistic approach - in a real scenario, you'd use jq for proper JSON manipulation
  if ! grep -q '"security.workspace.trust.enabled": false' .devcontainer/devcontainer.json; then
    echo "⚠️ devcontainer.json needs updating. Please ensure it contains workspace trust settings."
    echo "See docs/RESTRICTED_MODE_PREVENTION.md for details."
  fi
fi

# 10. Create a verification script that can be run to check status
cat << 'EOF' > verify_standard_mode.sh
#!/bin/bash
# Verify that standard mode is active and restricted mode is disabled

echo "Verifying standard mode status..."

# Check environment variables
if [ "$STANDARD_MODE" = "true" ] && [ "$USE_RECOVERY_MODE" = "false" ]; then
  echo "✅ Environment variables are correctly set"
else
  echo "❌ Environment variables are not correctly set:"
  echo "   STANDARD_MODE=$STANDARD_MODE"
  echo "   USE_RECOVERY_MODE=$USE_RECOVERY_MODE"
fi

# Check VS Code settings
if [ -f .vscode/settings.json ]; then
  if grep -q '"security.workspace.trust.enabled": false' .vscode/settings.json; then
    echo "✅ VS Code workspace trust is disabled in settings.json"
  else
    echo "❌ VS Code workspace trust is not properly configured in settings.json"
  fi
else
  echo "❌ .vscode/settings.json file not found"
fi

# Check marker files
if [ -f .standard_mode ]; then
  echo "✅ Standard mode marker file exists"
else
  echo "❌ Standard mode marker file missing"
fi

# Check global VS Code settings if in Codespace
if [ -d "/home/codespace/.vscode-remote/data/Machine" ]; then
  GLOBAL_SETTINGS="/home/codespace/.vscode-remote/data/Machine/settings.json"
  if [ -f "$GLOBAL_SETTINGS" ] && grep -q '"security.workspace.trust.enabled": false' "$GLOBAL_SETTINGS"; then
    echo "✅ Global VS Code settings have workspace trust disabled"
  else
    echo "❌ Global VS Code settings do not have workspace trust disabled"
  fi
fi

# Overall status
echo ""
echo "If any ❌ errors were shown above, run ./fix_restricted_mode.sh to fix them"
echo "If problems persist, try rebuilding the container with:"
echo "  - VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)"
echo "  - Type and select 'Codespaces: Rebuild Container'"
EOF

chmod +x verify_standard_mode.sh

echo "✅ Restricted mode prevention complete!"
echo "To verify the fix worked, run: ./verify_standard_mode.sh"