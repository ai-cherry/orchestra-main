#!/bin/bash
# Quick dependabot cleanup script
echo "🧹 Cleaning up dependabot PRs..."
python3 github_cli_manager.py cleanup --execute
