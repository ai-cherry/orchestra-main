#!/bin/bash
# One-command setup for cherry_ai Version Management
# Just run: ./setup_version_management.sh

set -euo pipefail

echo "🚀 Setting up automated version management..."

# Make scripts executable
chmod +x scripts/setup_version_management.sh
chmod +x scripts/*.py

# Run the full setup
./scripts/setup_version_management.sh

echo "✅ Setup complete! Version management is now fully automated."