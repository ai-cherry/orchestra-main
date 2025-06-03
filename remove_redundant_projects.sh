#!/bin/bash

# Remove Redundant UI Projects Script
# WARNING: Only run this AFTER reviewing backups and migrating needed components

set -e

echo "🗑️  Removing Redundant UI Projects..."
echo "⚠️  WARNING: This will permanently delete redundant UI directories!"
echo "   Make sure you've reviewed the backup and migrated needed components."

read -p "Are you sure you want to proceed? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled."
    exit 1
fi

echo -e "\n📝 Projects to be removed:"
echo "  • dashboard/ (Next.js project)"
echo "  • src/ui/web/react_app/ (Duplicate React project)"

# Remove dashboard project
if [ -d "dashboard" ]; then
    echo -e "\n🗑️  Removing dashboard/"
    rm -rf dashboard/
    echo "   ✅ dashboard/ removed"
fi

# Remove react_app project  
if [ -d "src/ui/web/react_app" ]; then
    echo -e "\n🗑️  Removing src/ui/web/react_app/"
    rm -rf src/ui/web/react_app/
    echo "   ✅ src/ui/web/react_app/ removed"
fi

# Clean up empty directories
if [ -d "src/ui/web" ] && [ -z "$(ls -A src/ui/web)" ]; then
    rmdir src/ui/web
    echo "   ✅ Empty src/ui/web/ removed"
fi

if [ -d "src/ui" ] && [ -z "$(ls -A src/ui)" ]; then
    rmdir src/ui
    echo "   ✅ Empty src/ui/ removed"
fi

echo -e "\n🎯 Consolidation Complete!"
echo "📋 Remaining UI structure:"
echo "  ✅ admin-ui/ (PRIMARY - Active React + Vite project)"
echo "  📦 Backups preserved in: ui_projects_backup_*/"

echo -e "\n🔧 Next steps:"
echo "  1. Test admin-ui functionality: cd admin-ui && npm run dev"
echo "  2. Migrate any missing components from backups if needed"
echo "  3. Update deployment scripts to use only admin-ui"
echo "  4. Update documentation to reflect new structure"

echo -e "\n✅ UI Projects consolidation completed successfully!" 