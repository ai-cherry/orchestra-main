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
   - Creating a `~/.gcp` directory
   - Storing your service account credentials securely
   - Configuring gcloud CLI to use these credentials
   - Setting environment variables for consistent authentication

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

You can verify the setup by running:

```bash
gcloud auth list
```

You should see `orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com` listed as the active account.

## Troubleshooting

If you encounter authentication issues:

1. Check if the `GCP_MASTER_SERVICE_JSON` secret is correctly set in your GitHub repository
2. Verify the service account has the necessary permissions in your GCP project
3. Review the Codespace creation logs for any errors
