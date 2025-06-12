#!/bin/bash

# Force Vercel Deployment Script
echo "🚀 Forcing Vercel deployment with timestamp update..."

# Add a timestamp comment to package.json to trigger a change
TIMESTAMP=$(date +%s)
sed -i.bak "s/\"version\": \"0.0.0\"/\"version\": \"0.0.0-$TIMESTAMP\"/" package.json

# Remove backup
rm package.json.bak

echo "✅ Updated package.json with timestamp: $TIMESTAMP"
echo "📦 Building and deploying..."

# Build and deploy
npm run build
npx vercel --prod --yes

echo "🎯 Deployment initiated. Check status with: npx vercel ls" 