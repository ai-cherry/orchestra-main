#!/bin/bash

echo "🛑 STARTING ROO & CONTINUE.DEV CLEANUP..."

# Remove all Roo-related files
echo "Removing Roo configuration files..."
rm -rf .roo/
rm -f .roomodes*
rm -f complete_roo_setup.sh
rm -f manage_roo_system.sh
rm -f mcp_roo_server.py
rm -f start_roo_dev.sh
rm -f setup_roo_complete.sh
rm -f roo_integration.db
rm -f test_roo_integration.py

echo "Removing Roo legacy components..."
rm -f legacy/mcp_server/adapters/roo_adapter.py
rm -f ai_components/coordination/roo_mcp_adapter.py
rm -f ai_components/tests/test_roo_integration.py

echo "Removing Roo archive scripts..."
rm -f archive/one-time-scripts/test_roo_integration*.py

echo "Removing Roo database migrations..."
rm -f migrations/004_roo_integration_tables.sql

echo "Removing Roo requirements..."
rm -f requirements/minimal_roo.txt
rm -f requirements/roo_integration.txt

echo "Removing Roo automation scripts..."
rm -f scripts/auto_start_orchestra_roo.py
rm -f scripts/complete_roo_integration_setup.py

# Clean up any continue.dev references
echo "Removing Continue.dev references..."
rm -rf .continue/
rm -f continue.json
rm -f .vscode/continue.json

# Clean up git references to continue.dev branches
echo "Cleaning up git references..."
git branch -D feature/continue-setup-and-optimizations 2>/dev/null || true

echo "✅ ROO & CONTINUE.DEV CLEANUP COMPLETE!"
echo ""
echo "🚀 READY FOR CURSOR AI OPTIMIZATION SETUP"

