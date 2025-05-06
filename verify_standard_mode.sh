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

# Check additional environment variables
if [ "$VSCODE_DISABLE_WORKSPACE_TRUST" = "true" ] && [ "$DISABLE_WORKSPACE_TRUST" = "true" ]; then
  echo "✅ Additional workspace trust variables are correctly set"
else
  echo "❌ Additional workspace trust variables are not correctly set:"
  echo "   VSCODE_DISABLE_WORKSPACE_TRUST=$VSCODE_DISABLE_WORKSPACE_TRUST"
  echo "   DISABLE_WORKSPACE_TRUST=$DISABLE_WORKSPACE_TRUST"
fi

# Check VS Code settings
if [ -f .vscode/settings.json ]; then
  if grep -q '"security.workspace.trust.enabled": false' .vscode/settings.json; then
    echo "✅ VS Code workspace trust is disabled in settings.json"
  else
    echo "❌ VS Code workspace trust is not properly configured in settings.json"
  fi
  
  # Check for other required settings
  MISSING_SETTINGS=0
  if ! grep -q '"security.workspace.trust.startupPrompt": "never"' .vscode/settings.json; then
    echo "❌ Missing setting: security.workspace.trust.startupPrompt"
    MISSING_SETTINGS=1
  fi
  if ! grep -q '"security.workspace.trust.banner": "never"' .vscode/settings.json; then
    echo "❌ Missing setting: security.workspace.trust.banner"
    MISSING_SETTINGS=1
  fi
  if ! grep -q '"security.workspace.trust.emptyWindow": false' .vscode/settings.json; then
    echo "❌ Missing setting: security.workspace.trust.emptyWindow"
    MISSING_SETTINGS=1
  fi
  
  if [ $MISSING_SETTINGS -eq 0 ]; then
    echo "✅ All required VS Code settings are present"
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

# Check shell configuration files
SHELL_CONFIG_FIXED=true
for config_file in ~/.bashrc ~/.profile ~/.bash_profile ~/.zshrc; do
  if [ -f "$config_file" ]; then
    if ! grep -q "STANDARD_MODE=true" "$config_file"; then
      echo "❌ $config_file does not have STANDARD_MODE set"
      SHELL_CONFIG_FIXED=false
    fi
  fi
done

if [ "$SHELL_CONFIG_FIXED" = true ]; then
  echo "✅ Shell configuration files have environment variables set"
fi

# Check if startup hook is installed
STARTUP_HOOK_INSTALLED=false
for config_file in ~/.bashrc ~/.profile ~/.bash_profile ~/.zshrc; do
  if [ -f "$config_file" ] && grep -q ".devcontainer/startup/prevent_restricted.sh" "$config_file"; then
    STARTUP_HOOK_INSTALLED=true
    break
  fi
done

if [ "$STARTUP_HOOK_INSTALLED" = true ]; then
  echo "✅ Startup hook is installed"
else
  echo "❌ Startup hook is not installed in any shell configuration file"
fi

# Overall status
echo ""
echo "If any ❌ errors were shown above, run ./fix_restricted_mode.sh to fix them"
echo "If problems persist, try rebuilding the container with:"
echo "  - VS Code Command Palette (Ctrl+Shift+P or Cmd+Shift+P)"
echo "  - Type and select 'Codespaces: Rebuild Container'"