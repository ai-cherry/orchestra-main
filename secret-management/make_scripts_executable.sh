#!/bin/bash
# Make all scripts in the secret-management directory executable

# Find all .sh and .py files and make them executable
find "$(dirname "$0")" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \;

echo "All scripts in the secret-management directory are now executable."
echo "You can now run the deploy script with: ./deploy_secret_manager.sh --project-id=your-project-id"
