#!/bin/bash
# Startup script to prevent VS Code Restricted Mode in GitHub Codespaces
# Add this to your devcontainer.json postCreateCommand to run automatically

# Set critical environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true

# Add to .bashrc for persistence
if [ -f ~/.bashrc ]; then
  # Remove any existing mode settings to avoid duplication
  grep -v "USE_RECOVERY_MODE\|STANDARD_MODE\|VSCODE_DISABLE_WORKSPACE_TRUST\|DISABLE_WORKSPACE_TRUST" ~/.bashrc > ~/.bashrc.tmp
  mv ~/.bashrc.tmp ~/.bashrc

  # Add the environment variables
  cat << 'EOF' >> ~/.bashrc

# Orchestra mode control environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true
EOF
fi

# Update VS Code settings
mkdir -p .vscode
if [ -f .vscode/settings.json ]; then
  # Basic sed approach since jq may not be available
  sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' .vscode/settings.json 2>/dev/null
  sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' .vscode/settings.json 2>/dev/null
  sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' .vscode/settings.json 2>/dev/null
  sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' .vscode/settings.json 2>/dev/null
else
  # Create new settings.json
  cat << EOF > .vscode/settings.json
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
fi

# Make all scripts executable
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null

echo "✅ Restricted mode prevention complete. VS Code should start in standard mode."
