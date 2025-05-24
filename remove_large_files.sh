#!/bin/bash
# Script to remove large files from git history

# Make sure we're in the right directory
cd /workspaces/orchestra-main

# Remove the large files from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch \
    google-cloud-sdk.staging/bin/anthoscli \
    google-cloud-cli-462.0.0-linux-x86_64.tar.gz \
    google-cloud-cli-465.0.0-linux-x86_64.tar.gz \
    google-cloud-sdk-426.0.0-linux-x86_64.tar.gz \
    google-cloud-sdk-latest-linux-x86_64.tar.gz" \
  --prune-empty --tag-name-filter cat -- --all

# Remove the refs/original created by filter-branch
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# Garbage collect to remove the old objects
git reflog expire --expire=now --all
git gc --prune=now

echo "Large files have been removed from git history."
echo "You can now try pushing to GitHub again."
