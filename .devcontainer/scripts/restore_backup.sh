#!/bin/bash
# Script to restore a previously backed up devcontainer configuration

set -e

# List available backups
echo "Available configuration backups:"
ls -la /workspaces/cherry_ai-main/.devcontainer/backups/

# Prompt for backup to restore
read -p "Enter backup directory name to restore (YYYYMMDD-HHMMSS format): " BACKUP_DIR

if [ ! -d "/workspaces/cherry_ai-main/.devcontainer/backups/${BACKUP_DIR}" ]; then
    echo "Error: Backup directory not found"
    exit 1
fi

# Confirm before proceeding
read -p "This will overwrite your current devcontainer configuration. Continue? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Restoration canceled"
    exit 0
fi

# Backup current configuration first
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "/workspaces/cherry_ai-main/.devcontainer/backups/${TIMESTAMP}-pre-restore"
cp /workspaces/cherry_ai-main/.devcontainer/Dockerfile "/workspaces/cherry_ai-main/.devcontainer/backups/${TIMESTAMP}-pre-restore/"
cp /workspaces/cherry_ai-main/.devcontainer/devcontainer.json "/workspaces/cherry_ai-main/.devcontainer/backups/${TIMESTAMP}-pre-restore/"
cp /workspaces/cherry_ai-main/.devcontainer/setup.sh "/workspaces/cherry_ai-main/.devcontainer/backups/${TIMESTAMP}-pre-restore/"

# Restore selected backup
cp "/workspaces/cherry_ai-main/.devcontainer/backups/${BACKUP_DIR}/Dockerfile" /workspaces/cherry_ai-main/.devcontainer/
cp "/workspaces/cherry_ai-main/.devcontainer/backups/${BACKUP_DIR}/devcontainer.json" /workspaces/cherry_ai-main/.devcontainer/
cp "/workspaces/cherry_ai-main/.devcontainer/backups/${BACKUP_DIR}/setup.sh" /workspaces/cherry_ai-main/.devcontainer/

echo "Configuration restored from backup: ${BACKUP_DIR}"
echo "A backup of your previous configuration was saved to: ${TIMESTAMP}-pre-restore"
echo "You'll need to rebuild the container for changes to take effect."
