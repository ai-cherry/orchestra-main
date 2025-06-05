#!/bin/bash

# 🚀 Deploy Cherry AI to Lambda Labs Production
# Usage: ./deploy_to_lambda.sh [branch]

BRANCH=${1:-main}
LAMBDA_IP="150.136.94.139"

echo "🚀 Deploying Cherry AI to Lambda Labs..."
echo "📍 Server: $LAMBDA_IP"
echo "🌿 Branch: $BRANCH"

# Push to GitHub first
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Deploy to Lambda Labs - $(date)"
git push origin $BRANCH

# Deploy to Lambda Labs
echo "🚀 Deploying to Lambda Labs..."
ssh ubuntu@$LAMBDA_IP << EOF
cd /opt/cherry-ai
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cherry-ai
sudo systemctl restart cherry-ai-bridge
sudo systemctl restart nginx
echo "✅ Deployment complete!"
