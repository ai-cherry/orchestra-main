#!/bin/bash
echo "Removing existing gcloud installation..."
rm -rf ~/google-cloud-sdk
rm -rf /workspaces/orchestra-main/google-cloud-sdk

echo "Downloading and installing gcloud SDK..."
curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts --install-dir=$HOME

echo "Setting up environment..."
export PATH=$PATH:$HOME/google-cloud-sdk/bin
echo 'export PATH=$PATH:$HOME/google-cloud-sdk/bin' >> ~/.bashrc

echo "Updating gcloud components..."
$HOME/google-cloud-sdk/bin/gcloud components update --quiet

echo "gcloud reinstalled successfully!"

echo "=== Fixing GCloud Authentication Issue ==="
echo

# Show current accounts
echo "Current accounts:"
gcloud auth list
echo

# Set the active account to your personal account
echo "Setting active account to your personal account..."
gcloud config set account scoobyjava@cherry-ai.me

# Verify the change
echo
echo "Verifying active account:"
gcloud config get-value account

# Set the project
echo
echo "Setting project..."
gcloud config set project cherry-ai-project

# Test authentication
echo
echo "Testing authentication..."
gcloud projects describe cherry-ai-project --format="value(projectId)" && echo "✅ Authentication working!" || echo "❌ Authentication failed"

echo
echo "Current configuration:"
gcloud config list

echo
echo "=== Now you can run deployment checks ==="
echo "Try these commands:"
echo "  gcloud builds list --limit=5"
echo "  gcloud run services list --region=us-central1"
echo "  gcloud logging read 'severity>=ERROR' --limit=10"
