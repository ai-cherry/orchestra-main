#!/bin/bash

# Restart Gemini Code Assist to apply all configurations
# This script will restart the VS Code Gemini extension

echo "Restarting Gemini Code Assist extension..."

# Set environment variable for Google Application Credentials
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/service-account.json

# Write the current credentials to the file
if [ ! -z "$GCP_PROJECT_MANAGEMENT_KEY" ]; then
  echo "$GCP_PROJECT_MANAGEMENT_KEY" > /tmp/service-account.json
  echo "Service account credentials saved to temporary file."
else
  echo "Warning: GCP_PROJECT_MANAGEMENT_KEY environment variable not set."
  echo "Authentication may fail without valid credentials."
fi

# Create a command to reload VS Code window
cat > /tmp/reload_vscode.js << EOL
const vscode = require('vscode');
vscode.commands.executeCommand('workbench.action.reloadWindow');
EOL

# Execute the reload command (this would work in a VS Code Task)
echo "To apply changes, please run the 'Developer: Reload Window' command in VS Code"
echo "  1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)"
echo "  2. Type 'reload window' and select 'Developer: Reload Window'"
echo ""
echo "After reloading, Gemini Code Assist should be properly connected to your codebase."
