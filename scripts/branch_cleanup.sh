#!/bin/bash
# Clean up merged branches
echo "🌿 Cleaning up merged branches..."
gh api repos/ai-cherry/orchestra-main/branches --jq '.[] | select(.name != "main") | .name' | while read branch; do
    echo "Checking branch: $branch"
    # Add logic to check if branch is merged and safe to delete
done
