#!/bin/bash
set -e

# Check if we are in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not in a git repository."
    exit 1
fi

# Get current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Create a new feature branch
timestamp=$(date +%Y%m%d%H%M%S)
branch_name="refactor/unified-registry-$timestamp"

echo "Creating new feature branch: $branch_name"
git checkout -b "$branch_name"

# Show changes
echo "Changes to be committed:"
git status --short

# Add all changes
echo "Adding all changes..."
git add .

# Commit with message
echo "Committing changes..."
git commit -m "refactor: consolidate parallel registry implementations" -m "Unified service and agent registries, added deprecation warnings, comprehensive tests and documentation"

# Push the branch
echo "Pushing branch to remote..."
git push -u origin "$branch_name"

echo ""
echo "========================================="
echo "Go to GitHub and create a PR from branch: $branch_name"
echo "Title: refactor: consolidate parallel registry implementations"
echo "========================================="
