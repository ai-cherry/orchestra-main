#!/bin/bash

# Orchestra AI Backup Script
BACKUP_DIR="$HOME/orchestra-dev/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="orchestra_backup_$DATE.tar.gz"

# Create backup
cd "$HOME/orchestra-dev"
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='logs' \
    --exclude='.git' \
    .

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t orchestra_backup_*.tar.gz | tail -n +11 | xargs rm -f

echo "$(date): Backup created: $BACKUP_FILE"
