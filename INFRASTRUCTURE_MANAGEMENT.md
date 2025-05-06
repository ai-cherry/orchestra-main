# AI Orchestra Infrastructure Management

This document provides a comprehensive guide to the infrastructure management system for the AI Orchestra project. It explains how to use the scripts and workflows to manage the GCP infrastructure, GitHub secrets, and Codespaces configuration.

## Overview

The AI Orchestra project uses a combination of service account keys and Workload Identity Federation (WIF) for authentication with GCP. The infrastructure management system consists of several scripts and workflows that work together to:

1. Create service account keys for Vertex AI and Gemini services
2. Update GitHub organization secrets with the new keys
3. Update GitHub Codespaces secrets with the new keys
4. Set up Workload Identity Federation for GitHub Actions
5. Test the integration between GitHub, Codespaces, and GCP
6. Update Terraform state

## Prerequisites

Before using the infrastructure management system, you need to have the following:

1. A GCP project with the necessary APIs enabled
2. A GitHub organization with the necessary repositories
3. A GitHub Personal Access Token (PAT) with the necessary permissions
4. A GCP service account key with the necessary permissions (GCP_MASTER_SERVICE_JSON)

## Scripts

The infrastructure management system consists of the following scripts:

### update_gcp_infrastructure.sh

This is the main script that orchestrates the entire infrastructure management process. It:

1. Authenticates with GCP using the GCP_MASTER_SERVICE_JSON
2. Creates service account keys for Vertex AI and Gemini services
3. Updates GitHub organization secrets with the new keys
4. Updates GitHub Codespaces secrets with the new keys
5. Sets up Workload Identity Federation for GitHub Actions
6. Tests the integration between GitHub, Codespaces, and GCP
7. Updates Terraform state

Usage:

```bash
export GCP_MASTER_SERVICE_JSON="<your-gcp-master-service-json>"
export GITHUB_TOKEN="<your-github-token>"
export GCP_PROJECT_ID="cherry-ai-project"
export GITHUB_ORG="ai-cherry"
export GITHUB_REPO="orchestra-main"
export REGION="us-central1"
export ENV="dev"
./update_gcp_infrastructure.sh
```

### create_badass_service_keys.sh

This script creates service account keys for Vertex AI and Gemini services, and updates GitHub organization secrets with the new keys.

Usage:

```bash
export GCP_MASTER_SERVICE_JSON="<your-gcp-master-service-json>"
export GITHUB_TOKEN="<your-github-token>"
export GCP_PROJECT_ID="cherry-ai-project"
export GITHUB_ORG="ai-cherry"
export GITHUB_REPO="orchestra-main"
export REGION="us-central1"
./create_badass_service_keys.sh
```

### scripts/update_codespaces_secrets.sh

This script updates GitHub Codespaces secrets with GCP credentials.

Usage:

```bash
export GITHUB_TOKEN="<your-github-token>"
export GCP_PROJECT_ID="cherry-ai-project"
export GITHUB_ORG="ai-cherry"
export GITHUB_REPO="orchestra-main"
export REGION="us-central1"
export GCP_VERTEX_POWER_KEY="<your-vertex-power-key>"
export GCP_GEMINI_POWER_KEY="<your-gemini-power-key>"
./scripts/update_codespaces_secrets.sh
```

### orchestra_wif_master.sh

This script sets up Workload Identity Federation for GitHub Actions.

Usage:

```bash
export GCP_MASTER_SERVICE_JSON="<your-gcp-master-service-json>"
export GITHUB_TOKEN="<your-github-token>"
export GCP_PROJECT_ID="cherry-ai-project"
export GITHUB_ORG="ai-cherry"
export GITHUB_REPO="orchestra-main"
export REGION="us-central1"
export POOL_ID="github-actions-pool"
export PROVIDER_ID="github-actions-provider"
./orchestra_wif_master.sh
```

### scripts/test_gcp_integration.sh

This script tests the integration between GitHub, Codespaces, and GCP.

Usage:

```bash
export GCP_PROJECT_ID="cherry-ai-project"
export REGION="us-central1"
./scripts/test_gcp_integration.sh
```

## GitHub Actions Workflows

The infrastructure management system includes the following GitHub Actions workflows:

### .github/workflows/update-gcp-infrastructure.yml

This workflow runs the update_gcp_infrastructure.sh script to update the GCP infrastructure. It can be triggered manually from the GitHub Actions tab.

### .github/workflows/infrastructure-sync.yml

This workflow uses Workload Identity Federation for authentication with GCP and runs the scripts to create service account keys and update GitHub secrets. It can be triggered manually from the GitHub Actions tab or automatically when changes are pushed to the main branch.

## Security Considerations

The infrastructure management system uses service account keys and Workload Identity Federation for authentication with GCP. Here are some security considerations:

1. Service account keys are highly privileged and should be protected
2. Service account keys are stored in GitHub secrets and Secret Manager
3. Workload Identity Federation is more secure than service account keys
4. Service account keys should be rotated regularly
5. Service account keys should be deleted from the filesystem after use

## Troubleshooting

If you encounter issues with the infrastructure management system, here are some troubleshooting steps:

1. Check the logs for error messages
2. Verify that the required environment variables are set
3. Verify that the required APIs are enabled
4. Verify that the service accounts have the necessary permissions
5. Verify that the GitHub secrets are set correctly
6. Verify that the Workload Identity Federation is set up correctly

## Next Steps

After setting up the infrastructure management system, you can:

1. Create a new Codespace or rebuild an existing one
2. Verify that the Codespace has access to GCP resources
3. Run the test_gcp_integration.sh script to verify the integration
4. Update the Terraform state if needed
5. Commit and push the changes to your repository

## Conclusion

The infrastructure management system provides a comprehensive solution for managing the GCP infrastructure, GitHub secrets, and Codespaces configuration for the AI Orchestra project. By following the instructions in this document, you can ensure that your infrastructure is properly set up and maintained.