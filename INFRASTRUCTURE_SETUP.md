# AI Orchestra Infrastructure Setup

This document provides instructions for setting up and managing the GCP infrastructure for the AI Orchestra project.

## Overview

The AI Orchestra project uses the following GCP resources:

- **Cloud Run**: For hosting the API and UI services
- **Firestore**: For storing data
- **Secret Manager**: For storing sensitive information
- **Vertex AI**: For AI model hosting and inference
- **Workload Identity Federation**: For secure authentication between GitHub and GCP

## Prerequisites

Before you begin, make sure you have the following:

1. **Google Cloud SDK**: Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. **Terraform**: The scripts will install Terraform if it's not already installed
3. **GitHub CLI**: The scripts will install the GitHub CLI if it's not already installed
4. **GitHub Personal Access Token**: With `repo` and `admin:org` scopes
5. **GCP Project**: A GCP project with billing enabled

## Setup Scripts

The following scripts are provided to help you set up and manage the infrastructure:

### 1. `fix_terraform_config.sh`

This script fixes common issues with the Terraform configuration:

- Resolves duplicate resource configurations
- Fixes duplicate backend configurations
- Resolves duplicate variable declarations
- Creates missing module directories
- Creates missing scripts

Usage:
```bash
chmod +x fix_terraform_config.sh
./fix_terraform_config.sh
```

### 2. `deploy_gcp_infrastructure.sh`

This script deploys the infrastructure to GCP:

- Installs Terraform if needed
- Authenticates with GCP
- Runs the Terraform configuration fix script
- Initializes Terraform
- Plans and applies Terraform changes
- Creates service account keys
- Updates GitHub secrets

Usage:
```bash
# Set required environment variables
export GCP_PROJECT_ID="cherry-ai-project"
export REGION="us-west4"
export ENV="dev"
export GCP_MASTER_SERVICE_JSON=$(cat /path/to/master-service-account-key.json)
export GITHUB_TOKEN="your_github_token"

# Run the deployment script
chmod +x deploy_gcp_infrastructure.sh
./deploy_gcp_infrastructure.sh
```

### 3. `update_github_org_secrets.sh`

This script updates GitHub organization secrets with GCP service account information:

- Installs GitHub CLI if needed
- Authenticates with GitHub
- Sets GCP project information secrets
- Sets service account email secrets
- Sets service account key secrets

Usage:
```bash
# Set required environment variables
export GCP_PROJECT_ID="cherry-ai-project"
export GITHUB_ORG="ai-cherry"
export REGION="us-west4"
export ENV="dev"
export GITHUB_TOKEN="your_github_token"

# Run the update script
chmod +x update_github_org_secrets.sh
./update_github_org_secrets.sh
```

## Infrastructure Components

### Service Accounts

The following service accounts are created:

1. **gcp-master-admin**: Master service account with owner permissions (used for initial setup)
2. **vertex-power-user**: Service account for Vertex AI operations
3. **gemini-power-user**: Service account for Gemini operations
4. **github-actions**: Service account for GitHub Actions workflows
5. **orchestrator-api**: Service account for the Orchestrator API
6. **phidata-agent-ui**: Service account for the Phidata Agent UI

### Workload Identity Federation

Workload Identity Federation is set up to allow GitHub Actions to authenticate with GCP without using service account keys. This is more secure than using service account keys directly.

The `orchestra_wif_master.sh` script sets up Workload Identity Federation:

```bash
# Set required environment variables
export GCP_PROJECT_ID="cherry-ai-project"
export GITHUB_ORG="ai-cherry"
export GITHUB_REPO="orchestra-main"
export REGION="us-west4"
export GCP_MASTER_SERVICE_JSON=$(cat /path/to/master-service-account-key.json)
export GITHUB_TOKEN="your_github_token"

# Run the WIF setup script
chmod +x orchestra_wif_master.sh
./orchestra_wif_master.sh
```

## GitHub Actions Workflows

The GitHub Actions workflows use Workload Identity Federation to authenticate with GCP. The following secrets are required:

- **GCP_PROJECT_ID**: The GCP project ID
- **GCP_REGION**: The GCP region
- **GCP_ENV**: The environment (dev, staging, prod)
- **WIF_PROVIDER_ID**: The Workload Identity Federation provider ID
- **GITHUB_ACTIONS_SERVICE_ACCOUNT**: The GitHub Actions service account email
- **ORCHESTRATOR_API_SERVICE_ACCOUNT**: The Orchestrator API service account email
- **PHIDATA_AGENT_UI_SERVICE_ACCOUNT**: The Phidata Agent UI service account email
- **VERTEX_POWER_USER_SERVICE_ACCOUNT**: The Vertex AI service account email
- **GEMINI_POWER_USER_SERVICE_ACCOUNT**: The Gemini service account email

These secrets are automatically set by the `update_github_org_secrets.sh` script.

## Troubleshooting

### Terraform Initialization Issues

If you encounter issues with Terraform initialization, run the `fix_terraform_config.sh` script to fix common issues.

### GitHub Authentication Issues

If you encounter issues with GitHub authentication, make sure your GitHub token has the required scopes (`repo` and `admin:org`).

### GCP Authentication Issues

If you encounter issues with GCP authentication, make sure your master service account key has the required permissions.

## Security Considerations

- The master service account has owner permissions, which is a security risk. Use it only for initial setup and then revoke its permissions.
- Service account keys are stored in Secret Manager, which is more secure than storing them in files.
- Workload Identity Federation is used to authenticate GitHub Actions with GCP, which is more secure than using service account keys directly.

## Next Steps

After setting up the infrastructure, you can:

1. Deploy the AI Orchestra application to Cloud Run
2. Set up CI/CD pipelines to automatically deploy changes
3. Configure monitoring and alerting
4. Set up logging and error tracking