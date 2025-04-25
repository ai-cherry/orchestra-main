#!/bin/bash
# Script to set up GCP authentication and generate new service account keys

set -e  # Exit on any error

echo "=== GCP Authentication Setup Script ==="
echo "Setting up authentication for project: agi-baby-cherry"

# Create a directory for credentials if it doesn't exist
mkdir -p /tmp/credentials

# Create a new service account key for the vertex-agent account
echo "Generating new service account key for vertex-agent..."
gcloud config set project agi-baby-cherry

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "GCloud not authenticated. Please run 'gcloud auth login' first."
    exit 1
fi

# Generate a new key for the vertex-agent service account
echo "Creating new key for vertex-agent@agi-baby-cherry.iam.gserviceaccount.com..."
gcloud iam service-accounts keys create /tmp/credentials/vertex-agent-new-key.json \
    --iam-account=vertex-agent@agi-baby-cherry.iam.gserviceaccount.com

# Backup existing key 
if [ -f /tmp/vertex-agent-key.json ]; then
    echo "Backing up existing key file..."
    cp /tmp/vertex-agent-key.json /tmp/vertex-agent-key.json.bak
fi

# Install the new key
echo "Installing new key to /tmp/vertex-agent-key.json..."
cp /tmp/credentials/vertex-agent-new-key.json /tmp/vertex-agent-key.json
chmod 600 /tmp/vertex-agent-key.json

# Set environment variables
echo "Setting up environment variables..."
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GCP_PROJECT_ID=agi-baby-cherry

# Add these to .bashrc for persistence
echo '# GCP Authentication' >> ~/.bashrc
echo 'export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json' >> ~/.bashrc
echo 'export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json' >> ~/.bashrc
echo 'export GCP_PROJECT_ID=agi-baby-cherry' >> ~/.bashrc

echo "=== Testing Authentication ==="
# Test authentication with new key
python test_gcp_auth.py

echo "=== Setting up Figma Integration ==="
# Set up Figma token
export FIGMA_PAT=figd_JbqWhdGvNaRvQyLdZdEJslu-8hHoaotLaNKByNRz
echo 'export FIGMA_PAT=figd_JbqWhdGvNaRvQyLdZdEJslu-8hHoaotLaNKByNRz' >> ~/.bashrc

echo "=== Setup Complete ==="
echo "You can now run memory and infrastructure validation tests."
