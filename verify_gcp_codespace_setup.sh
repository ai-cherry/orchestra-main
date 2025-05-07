#!/bin/bash
# Script to verify GCP authentication is correctly set up in Codespaces

echo "Verifying GCP Codespaces Setup..."
echo "=================================="

# Check if Google Cloud SDK is in PATH
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud command not found in PATH"
    echo "Adding gcloud SDK to PATH for this session..."
    export PATH=$PATH:/workspaces/orchestra-main/google-cloud-sdk/bin
    if ! command -v gcloud &> /dev/null; then
        echo "❌ ERROR: Could not find gcloud in /workspaces/orchestra-main/google-cloud-sdk/bin"
        echo "   Please check if the SDK is installed correctly."
        exit 1
    else
        echo "✅ Successfully added gcloud to PATH"
    fi
else
    echo "✅ gcloud command found in PATH"
fi

# Check if service account key file exists
if [ -f "$HOME/.gcp/service-account.json" ]; then
    echo "✅ Service account key file exists at $HOME/.gcp/service-account.json"
else
    echo "❌ Service account key file not found at $HOME/.gcp/service-account.json"
    
    # Check if we need to create the directory and copy the file
    if [ -f "/workspaces/orchestra-main/service-account-key.json" ]; then
        echo "   Found service account key at /workspaces/orchestra-main/service-account-key.json"
        echo "   Creating directory and copying file..."
        mkdir -p $HOME/.gcp
        cp /workspaces/orchestra-main/service-account-key.json $HOME/.gcp/service-account.json
        echo "✅ Service account key file copied to $HOME/.gcp/service-account.json"
    else
        echo "❌ ERROR: Could not find service account key file to copy"
        exit 1
    fi
fi

# Verify gcloud authentication
echo -e "\nChecking gcloud authentication..."
AUTH_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)

if [[ "$AUTH_ACCOUNT" == "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com" ]]; then
    echo "✅ Authenticated as orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
else
    echo "❌ Not authenticated as orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
    echo "   Current authentication: $AUTH_ACCOUNT"
    
    # Try to authenticate
    echo "   Attempting to authenticate..."
    gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=$HOME/.gcp/service-account.json
    
    # Check again
    AUTH_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
    if [[ "$AUTH_ACCOUNT" == "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com" ]]; then
        echo "✅ Successfully authenticated as orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
    else
        echo "❌ ERROR: Failed to authenticate"
        exit 1
    fi
fi

# Verify project is set correctly
echo -e "\nChecking GCP project..."
PROJECT=$(gcloud config get-value project 2>/dev/null)

if [[ "$PROJECT" == "cherry-ai-project" ]]; then
    echo "✅ Project is set to cherry-ai-project"
else
    echo "❌ Project is not set to cherry-ai-project"
    echo "   Current project: $PROJECT"
    
    # Try to set the project
    echo "   Setting project to cherry-ai-project..."
    gcloud config set project cherry-ai-project
    
    # Check again
    PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [[ "$PROJECT" == "cherry-ai-project" ]]; then
        echo "✅ Successfully set project to cherry-ai-project"
    else
        echo "❌ ERROR: Failed to set project"
        exit 1
    fi
fi

# Verify GOOGLE_APPLICATION_CREDENTIALS is set correctly
echo -e "\nChecking GOOGLE_APPLICATION_CREDENTIALS environment variable..."
if [[ "$GOOGLE_APPLICATION_CREDENTIALS" == "$HOME/.gcp/service-account.json" ]]; then
    echo "✅ GOOGLE_APPLICATION_CREDENTIALS is set to $HOME/.gcp/service-account.json"
else
    echo "❌ GOOGLE_APPLICATION_CREDENTIALS is not set correctly"
    echo "   Current value: $GOOGLE_APPLICATION_CREDENTIALS"
    
    # Try to set the environment variable
    echo "   Setting GOOGLE_APPLICATION_CREDENTIALS..."
    export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
    
    # Check if it's in .bashrc
    if ! grep -q "export GOOGLE_APPLICATION_CREDENTIALS=" $HOME/.bashrc; then
        echo "   Adding GOOGLE_APPLICATION_CREDENTIALS to .bashrc..."
        echo "export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json" >> $HOME/.bashrc
    fi
    
    echo "✅ Successfully set GOOGLE_APPLICATION_CREDENTIALS to $HOME/.gcp/service-account.json"
fi

# Verify SDK path is in .bashrc
echo -e "\nChecking if Google Cloud SDK path is in .bashrc..."
if grep -q "export PATH=.*google-cloud-sdk/bin" $HOME/.bashrc; then
    echo "✅ Google Cloud SDK path is in .bashrc"
else
    echo "❌ Google Cloud SDK path is not in .bashrc"
    echo "   Adding it now..."
    echo "export PATH=\$PATH:/workspaces/orchestra-main/google-cloud-sdk/bin" >> $HOME/.bashrc
    echo "✅ Successfully added Google Cloud SDK path to .bashrc"
fi

# Final verification summary
echo -e "\n=================================="
echo "✅ GCP Codespaces setup verification completed successfully!"
echo "✅ Authentication: orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com"
echo "✅ Project: cherry-ai-project"
echo "✅ Credentials path: $HOME/.gcp/service-account.json"
echo "=================================="
echo -e "\nYou can now use GCP services in your Codespaces environment."
echo "To apply the environment variables to your current session, run: source ~/.bashrc"
