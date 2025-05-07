# GitHub Codespaces GCP Authentication Setup

This document explains how to use the devcontainer.json configuration to establish persistent authentication with Google Cloud Platform in GitHub Codespaces.

## Prerequisites

Before launching a Codespace, you need to set up the following:

1. **Create Service Account Key**: Ensure you have a JSON key file for your service account `orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com`

2. **Add GitHub Secret**: 
   - Go to your GitHub repository settings (https://github.com/ai-cherry/orchestra-main)
   - Navigate to Settings > Secrets and variables > Actions
   - Create a new repository secret named `GCP_MASTER_SERVICE_JSON`
   - Paste the entire JSON content of your service account key file as the value

## How It Works

The devcontainer.json configuration in this repository:

1. Uses the `mcr.microsoft.com/devcontainers/universal:2` base image
2. Installs the Google Cloud SDK
3. Sets up persistent authentication by:
   - Creating a `$HOME/.gcp` directory
   - Storing your service account credentials securely
   - Configuring gcloud CLI to use these credentials
   - Setting environment variables for consistent authentication
   - Adding the Google Cloud SDK to PATH
   - Disabling interactive prompts for gcloud commands

## Usage

1. The devcontainer.json file is already placed in the `.devcontainer` directory of this repository.

2. To use this configuration:
   - Click the green "Code" button on your repository
   - Select the "Codespaces" tab
   - Click "Create codespace on main"

3. When the Codespace launches, it will automatically:
   - Install the required tools
   - Set up authentication with your GCP project
   - Configure the environment for development

4. Upon successful setup, you'll have authenticated access to your GCP project without URL-based authentication prompts.

## Verifying Setup

We've provided a verification script to ensure your GCP authentication is set up correctly:

```bash
./verify_gcp_codespace_setup.sh
```

This script will:
- Check if the Google Cloud SDK is in your PATH
- Verify the service account key file exists
- Confirm you're authenticated with the correct service account
- Ensure the project is set to cherry-ai-project
- Validate the GOOGLE_APPLICATION_CREDENTIALS environment variable is set properly
- Make any necessary corrections if issues are found

You can also manually verify the core setup elements by running:

```bash
# Check authenticated account
gcloud auth list

# Check current project
gcloud config get-value project

# Check credentials path
echo $GOOGLE_APPLICATION_CREDENTIALS
```

You should see `orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com` as the active account, `cherry-ai-project` as the project, and the path to your service account JSON file.

## Troubleshooting

If you encounter authentication issues:

1. Run the verification script to diagnose and fix common issues:
   ```bash
   ./verify_gcp_codespace_setup.sh
   ```

2. Check if the `GCP_MASTER_SERVICE_JSON` secret is correctly set in your GitHub repository

3. Verify the service account has the necessary permissions in your GCP project

4. Ensure the Google Cloud SDK is in your PATH:
   ```bash
   export PATH=$PATH:/workspaces/orchestra-main/google-cloud-sdk/bin
   ```

5. If changes were made to your .bashrc file, apply them to your current session:
   ```bash
   source ~/.bashrc
   ```

6. If you're still having issues, you may need to rebuild your Codespace container by:
   - Closing the Codespace
   - Reopening it
   - Click the "Rebuild Container" option
