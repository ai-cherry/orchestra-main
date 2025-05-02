#!/bin/bash

# Setup Script for Installing Google Cloud SDK
# Project: orchestra-main
# Purpose: Installs necessary tools for migration to Google Cloud Workstations and Vertex AI IDE

echo "Starting installation of Google Cloud SDK and related tools..."

# Step 1: Update package lists
echo "Updating package lists..."
sudo apt-get update

# Step 2: Install prerequisites
echo "Installing prerequisites..."
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl

# Step 3: Add Google Cloud SDK repository
echo "Adding Google Cloud SDK repository..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Step 4: Update package lists again and install Google Cloud SDK
echo "Installing Google Cloud SDK..."
sudo apt-get update
sudo apt-get install -y google-cloud-sdk

# Step 5: Verify installation
echo "Verifying Google Cloud SDK installation..."
gcloud --version

# Step 6: Install additional tools if needed
echo "Installing additional tools for development environment..."
sudo apt-get install -y python3 python3-pip
pip3 install poetry
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

echo "Google Cloud SDK and additional tools installation completed."
echo "You can now proceed with running the migration script 'migration_to_gcp.sh'."