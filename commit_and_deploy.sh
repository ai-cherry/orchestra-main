#!/bin/bash
set -e

echo "🚀 Preparing to commit and deploy simplification changes..."

# First, ensure we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Not in the project root directory"
    exit 1
fi

# Add all modified files
echo "📝 Adding modified files to git..."
git add Dockerfile
git add .cursorignore
git add .cursor/rules/*.mdc
git add deployment_simplification_commit.md
git add commit_and_deploy.sh

# Show what will be committed
echo "📋 Files to be committed:"
git status --short

# Commit with our detailed message
echo "💾 Creating commit..."
git commit -F deployment_simplification_commit.md

# Show the commit
echo "✅ Commit created:"
git log -1 --oneline

# Ask for confirmation before pushing
echo ""
echo "🤔 Ready to push to main and trigger deployment?"
echo "This will:"
echo "  1. Push to GitHub main branch"
echo "  2. Trigger DigitalOcean deployment via GitHub Actions"
echo "  3. Deploy to DigitalOcean App Platform"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Pushing to main branch..."
    git push origin main
    echo ""
    echo "✅ Push complete! DigitalOcean deployment pipeline triggered."
    echo ""
    echo "📊 Monitor progress at:"
    echo "  GitHub Actions: https://github.com/[your-repo]/actions"
    echo "  DigitalOcean App: https://cloud.digitalocean.com/apps"
else
    echo "❌ Push cancelled. Your changes are committed locally."
    echo "To push later, run: git push origin main"
fi
