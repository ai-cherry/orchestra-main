#!/bin/bash
# Script to backup the current stable devcontainer configuration

set -e
echo "Backing up current stable devcontainer configuration..."

# Create backup directory with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/workspaces/orchestra-main/.devcontainer/backups/${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

# Copy current configuration files
cp /workspaces/orchestra-main/.devcontainer/Dockerfile "$BACKUP_DIR"/
cp /workspaces/orchestra-main/.devcontainer/devcontainer.json "$BACKUP_DIR"/
cp /workspaces/orchestra-main/.devcontainer/setup.sh "$BACKUP_DIR"/

echo "Configuration backed up to: $BACKUP_DIR"
echo "To restore this configuration if needed, copy files back from this directory."
