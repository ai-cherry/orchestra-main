# Hybrid GCP Development Environment Setup

This document explains how to set up a hybrid development environment that integrates GitHub Codespaces with Google Cloud Platform's IDE solutions.

## Overview

This setup provides a seamless development experience across three environments:

1. **GitHub Codespaces** - Cloud-based VSCode environment
2. **Cloud Workstation** - A fully managed Google Cloud development environment 
3. **Vertex AI Workbench** - A managed JupyterLab environment for data science and ML workflows

All three environments use the same service account for authentication and clone the same repository, ensuring consistent access to your code and GCP resources.

## Step 1: Set Up GitHub Codespaces

### Prerequisites

1. **Create Service Account Key**: Ensure you have a JSON key file for your service account `orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com`

2. **Add GitHub Secret**: 
   - Go to your GitHub repository settings (https://github.com/ai-cherry/orchestra-main)
   - Navigate to Settings > Secrets and variables > Actions
   - Create a new repository secret named `GCP_MASTER_SERVICE_JSON`
   - Paste the entire JSON content of your service account key file as the value

### Launch Codespaces

The `.devcontainer/devcontainer.json` configuration in this repository:

1. Uses the `mcr.microsoft.com/devcontainers/universal:2` base image
2. Installs the Google Cloud SDK
3. Sets up persistent authentication with your GCP project

To launch Codespaces:
1. Click the green "Code" button on your repository
2. Select the "Codespaces" tab
3. Click "Create codespace on main"

## Step 2: Provision GCP IDEs

Once your Codespace is running and authenticated with GCP, you can provision the Google Cloud development environments:

### Using the Script

The included `setup-gcp-ides.sh` script will provision both a Cloud Workstation and a Vertex AI Workbench instance.

1. Run the script:
   ```bash
   ./setup-gcp-ides.sh
   ```

2. The script will:
   - Verify your service account exists and has proper permissions
   - Enable required APIs if they're not already enabled
   - Create a Cloud Workstation configuration and instance
   - Create a Vertex AI Workbench notebook
   - Display URLs to access your new environments

### Script Customization

You can customize the script by modifying the parameters at the top:

- **GCP Project Configuration**:
  - `PROJECT_ID`: Your Google Cloud project ID
  - `LOCATION`: Region for Cloud Workstation deployment
  - `ZONE`: Zone for Vertex AI Workbench deployment
  - `SERVICE_ACCOUNT`: Service account used by the environments

- **Instance Configuration**:
  - `WORKSTATION_CONFIG`: Name for your Cloud Workstation configuration
  - `WORKSTATION_NAME`: Name for your Cloud Workstation instance
  - `NOTEBOOK_NAME`: Name for your Vertex AI Workbench notebook
  - `WORKSTATION_MACHINE_TYPE`: Machine type for Cloud Workstation
  - `NOTEBOOK_MACHINE_TYPE`: Machine type for Vertex AI Workbench

- **Repository Configuration**:
  - `REPO_URL`: Your GitHub repository URL
  - `GITHUB_TOKEN`: Optional Personal Access Token for private repositories

## Step 3: Access Your Development Environments

After provisioning, you'll have access to three integrated development environments:

### 1. GitHub Codespaces
- Access through GitHub's web interface
- Full VSCode functionality in the browser
- Pre-authenticated with your GCP service account

### 2. Cloud Workstation
- Access from the Cloud Console: https://console.cloud.google.com/workstations/list
- Full development environment with VS Code interface
- Repository is pre-cloned during setup

### 3. Vertex AI Workbench
- Access from the Cloud Console: https://console.cloud.google.com/vertex-ai/workbench/list/instances
- Ideal for data science and ML workflows
- Jupyter-based environment with repository pre-cloned

## Private Repository Access

If your repository is private, you'll need to:

1. Generate a GitHub Personal Access Token with `repo` scope
2. Add the token to the `GITHUB_TOKEN` variable in the script
3. The script will automatically use the token when cloning the repository

## Resource Cleanup

When you no longer need the GCP environments:

1. Run the script with the cleanup parameter:
   ```bash
   ./setup-gcp-ides.sh cleanup
   ```

2. This will delete:
   - The Vertex AI Workbench notebook
   - The Cloud Workstation instance
   - The Cloud Workstation configuration

## Troubleshooting

If you encounter issues:

1. Verify service account permissions:
   ```bash
   gcloud projects get-iam-policy cherry-ai-project \
     --format="table(bindings.role,bindings.members)" | grep orchestra-project-admin-sa
   ```

2. Ensure the required APIs are enabled:
   ```bash
   gcloud services list --enabled --project=cherry-ai-project | grep -E 'workstations|notebooks'
   ```

3. Check for more detailed error messages in the Cloud Console

## Synchronization

All three environments (Codespaces, Cloud Workstation, and Vertex AI Workbench) clone the same repository, ensuring code consistency. To synchronize changes:

1. Use git to push changes from any environment
2. Pull changes in the other environments
3. Consider using GitHub Codespaces as your primary environment for editing code, and the GCP environments for specialized tasks

This hybrid setup provides flexibility, allowing you to choose the best environment for specific tasks while maintaining consistent authentication and access to your code.
