#!/bin/bash

# UI Projects Consolidation Script for Orchestra AI
# Safely consolidates multiple UI projects into the primary admin-ui

set -e

echo "🔄 Starting UI Projects Consolidation..."
echo "📋 Current UI projects found:"
echo "  1. admin-ui/ (PRIMARY - React 18 + Vite)"
echo "  2. dashboard/ (Next.js - REDUNDANT)"
echo "  3. src/ui/web/react_app/ (React 18 - REDUNDANT)"

# Create backup directory
BACKUP_DIR="ui_projects_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "\n📦 Creating backups in $BACKUP_DIR..."

# Backup dashboard
if [ -d "dashboard" ]; then
    echo "  • Backing up dashboard/"
    cp -r dashboard "$BACKUP_DIR/"
fi

# Backup react_app
if [ -d "src/ui/web/react_app" ]; then
    echo "  • Backing up src/ui/web/react_app/"
    cp -r src/ui/web/react_app "$BACKUP_DIR/"
fi

echo -e "\n🔍 Analyzing unique components that might need migration..."

# Check for unique components in dashboard
echo "=== Dashboard unique components ===" > "$BACKUP_DIR/analysis.txt"
find dashboard -name "*.tsx" -o -name "*.ts" | head -10 >> "$BACKUP_DIR/analysis.txt"
echo "" >> "$BACKUP_DIR/analysis.txt"

# Check for unique components in react_app
echo "=== React App unique components ===" >> "$BACKUP_DIR/analysis.txt"
find src/ui/web/react_app -name "*.tsx" -o -name "*.ts" | head -10 >> "$BACKUP_DIR/analysis.txt"
echo "" >> "$BACKUP_DIR/analysis.txt"

# Check admin-ui components for comparison
echo "=== Admin UI existing components ===" >> "$BACKUP_DIR/analysis.txt"
find admin-ui/src -name "*.tsx" -o -name "*.ts" | head -20 >> "$BACKUP_DIR/analysis.txt"

echo -e "\n⚠️  RECOMMENDATION: Review $BACKUP_DIR/analysis.txt before proceeding"
echo "   to ensure no critical functionality is lost."

echo -e "\n🎯 Next steps:"
echo "  1. Review backed up components"
echo "  2. Migrate any unique functionality to admin-ui/"
echo "  3. Run: ./remove_redundant_projects.sh"

echo -e "\n✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_DIR" 