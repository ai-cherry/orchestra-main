# GCP IDE Provisioning Guide

This document explains how to use the `provision_gcp_ide.sh` script to set up Google Cloud development environments.

## Overview

The script provisions two types of cloud development environments in your GCP project:

1. **Cloud Workstation** - A fully managed development environment accessible through a web browser
2. **Vertex AI Workbench** - A managed JupyterLab environment for data science and ML workflows

Both environments are configured with your service account and automatically clone your repository for immediate access to your code.

## Prerequisites

Before running this script, ensure you have:

1. Google Cloud CLI (`gcloud`) installed and configured
2. Authenticated with sufficient permissions to create resources in the `cherry-ai-project` project
3. Enabled the required APIs:
   - Cloud Workstations API
   - Notebooks API

You can enable these APIs with:
```bash
gcloud services enable workstations.googleapis.com notebooks.googleapis.com --project=cherry-ai-project
```

## Usage

1. Make the script executable (already done):
   ```bash
   chmod +x provision_gcp_ide.sh
   ```

2. Run the script:
   ```bash
   ./provision_gcp_ide.sh
   ```

3. The script will:
   - Verify your service account exists and has proper permissions
   - Create a Cloud Workstation configuration
   - Provision a Cloud Workstation instance
   - Create a Vertex AI Workbench notebook
   - Display URLs to access your new environments

## Integration with GitHub Codespaces

This script complements the GitHub Codespaces setup (`.devcontainer/devcontainer.json`):

- **GitHub Codespaces**: Uses the same service account for authentication
- **Cloud Environments**: The provisioned GCP environments use the same service account, creating a consistent development experience across all platforms
- **Repository Access**: All environments are configured to clone your repository, ensuring code consistency

## Customization

You can customize the script by modifying the configuration variables at the top:

- `PROJECT_ID`: Your Google Cloud project ID
- `LOCATION`: Region for Cloud Workstation deployment
- `ZONE`: Zone for Vertex AI Workbench deployment
- `SERVICE_ACCOUNT`: Service account used by the environments
- `REPO_URL`: GitHub repository to clone
- `WORKSTATION_CONFIG`: Name of the Cloud Workstation configuration
- `WORKSTATION_NAME`: Name of the Cloud Workstation instance
- `NOTEBOOK_NAME`: Name of the Vertex AI Workbench notebook

## Resource Cleanup

The script includes a commented-out cleanup function. To use it:

1. Edit the script and uncomment the `cleanup_resources` line at the bottom
2. Run the script to delete all created resources
3. Remember to comment out the line again if you re-run the script to create new resources

## Troubleshooting

If you encounter issues:

1. Ensure the service account has the necessary IAM roles:
   - `roles/workstations.workstationCreator`
   - `roles/notebooks.admin`

2. Verify you have quota available for the requested resources

3. Check for more detailed error messages in the Cloud Console
