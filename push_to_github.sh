#!/bin/bash
set -e

# Set git config
git config --global user.name "scoobyjava"
git config --global user.email "musillynn@gmail.com"

# Create credentials file
# echo "https://scoobyjava:YOUR_TOKEN@github.com" > ~/.git-credentials  # Removed PAT for security
# git config --global credential.helper store

# Push to GitHub
echo "Pushing to GitHub..."
git push origin main  # Use SSH or credential helper, do not hardcode PAT

echo "Push complete!"
