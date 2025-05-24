#!/bin/bash
# Script to remove large files from git history using filter-branch

# Make sure we're in the right directory
cd /workspaces/orchestra-main

# List of large files to remove
LARGE_FILES=(
  "google-cloud-sdk.staging/bin/anthoscli"
  "google-cloud-cli-462.0.0-linux-x86_64.tar.gz"
  "google-cloud-cli-465.0.0-linux-x86_64.tar.gz"
  "google-cloud-sdk-426.0.0-linux-x86_64.tar.gz"
  "google-cloud-sdk-latest-linux-x86_64.tar.gz"
)

# Create the filter command
FILTER_COMMAND="git rm --cached --ignore-unmatch"
for file in "${LARGE_FILES[@]}"; do
  FILTER_COMMAND+=" \"$file\""
done

# Remove the large files from git history
git filter-branch --force --index-filter "$FILTER_COMMAND" --prune-empty --tag-name-filter cat -- --all

# Remove the refs/original created by filter-branch
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# Garbage collect to remove the old objects
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "Large files have been removed from git history."
echo "Now force pushing to GitHub..."

# Force push to GitHub
git push origin main --force

echo "Push complete. Check for any errors in the output above."
