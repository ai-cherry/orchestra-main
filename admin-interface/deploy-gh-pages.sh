#!/bin/bash
set -e

echo "🚀 Deploying to GitHub Pages..."

# Build the application
npm run build

# Create temporary directory for gh-pages
rm -rf /tmp/gh-pages-deploy
mkdir -p /tmp/gh-pages-deploy
cp -r dist/* /tmp/gh-pages-deploy/

# Switch to gh-pages branch
git checkout -B gh-pages
git rm -rf . || true
cp -r /tmp/gh-pages-deploy/* .
echo "orchestra-admin.github.io" > CNAME

# Commit and push
git add .
git commit -m "Deploy to GitHub Pages: $(date)"
git push origin gh-pages --force

# Switch back to main
git checkout main

echo "✅ Deployed to GitHub Pages"
echo "URL: https://ai-cherry.github.io/orchestra-main/"
