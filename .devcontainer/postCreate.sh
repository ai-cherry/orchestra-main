#!/bin/bash
echo "Running postCreateCommand..."

echo "Installing Google Cloud CLI..."
# Install necessary dependencies
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl

# Add the Google Cloud SDK distribution URI as a package source
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import the Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Update and install the Cloud SDK
sudo apt-get update
sudo apt-get install -y google-cloud-cli

# Create venv if it doesn't exist
python3 -m venv .venv

# Activate & Install deps using unified script
# Ensures Python dependencies are installed AFTER base tools are ready
echo "Installing Python dependencies via unified_setup.sh..."
source .venv/bin/activate && ./unified_setup.sh # This should handle pip installs

echo "postCreateCommand finished."
