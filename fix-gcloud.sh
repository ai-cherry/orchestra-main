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
