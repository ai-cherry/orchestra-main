# Infrastructure Management System

This document provides an overview of the infrastructure management system for the AI Orchestra project. The system is designed to automate the setup and management of the GCP infrastructure, GitHub secrets, and Codespaces configuration.

## Overview

The infrastructure management system consists of several components:

1. **Scripts**: A collection of shell scripts that automate various tasks related to infrastructure management.
2. **GitHub Actions Workflows**: Workflows that run the scripts automatically when triggered.
3. **Terraform Modules**: Modules that define the infrastructure as code.

## Scripts

### `scripts/verify_gcp_setup.sh`

This script verifies that the GCP infrastructure is correctly set up. It checks:

- GCP project exists and is accessible
- Required APIs are enabled
- Service accounts exist
- Secret Manager secrets exist
- Terraform state bucket exists
- Vertex AI is accessible
- GitHub secrets are set

Usage:

```bash
./scripts/verify_gcp_setup.sh
```

### `scripts/update_github_org_secrets.sh`

This script updates GitHub organization secrets with GCP service account keys. It:

- Authenticates with GitHub using a personal access token
- Authenticates with GCP using the master service account key
- Gets service account keys from Secret Manager
- Updates GitHub organization secrets

Usage:

```bash
export GITHUB_TOKEN="your_github_token"
export GCP_MASTER_SERVICE_JSON="$(cat /path/to/master-key.json)"
./scripts/update_github_org_secrets.sh
```

### `scripts/update_codespaces_secrets.sh`

This script updates GitHub Codespaces secrets with GCP service account keys. It:

- Authenticates with GitHub using a personal access token
- Authenticates with GCP using the master service account key
- Gets service account keys from Secret Manager
- Updates GitHub Codespaces secrets

Usage:

```bash
export GITHUB_TOKEN="your_github_token"
export GCP_MASTER_SERVICE_JSON="$(cat /path/to/master-key.json)"
./scripts/update_codespaces_secrets.sh
```

### `scripts/create_powerful_service_keys.sh`

This script creates powerful service account keys for Vertex AI and Gemini. It:

- Authenticates with GCP using the master service account key
- Creates service accounts with powerful permissions
- Creates service account keys
- Stores the keys in Secret Manager

Usage:

```bash
export GCP_MASTER_SERVICE_JSON="$(cat /path/to/master-key.json)"
./scripts/create_powerful_service_keys.sh
```

### `scripts/test_gcp_integration.sh`

This script tests the integration between GitHub, Codespaces, and GCP. It:

- Authenticates with GCP using the master service account key
- Tests GCP project access
- Tests Secret Manager access
- Tests Vertex AI access
- Tests Cloud Storage access
- Tests IAM access
- Tests Vertex AI service account key
- Tests Gemini service account key

Usage:

```bash
export GCP_MASTER_SERVICE_JSON="$(cat /path/to/master-key.json)"
./scripts/test_gcp_integration.sh
```

## GitHub Actions Workflows

### `.github/workflows/infrastructure-sync.yml`

This workflow runs the infrastructure setup scripts automatically when triggered. It:

- Authenticates with GCP using Workload Identity Federation
- Runs the infrastructure setup scripts
- Verifies the setup
- Updates GitHub secrets
- Updates Codespaces secrets

Usage:

1. Go to the GitHub Actions tab in your repository
2. Select the "Infrastructure Sync" workflow
3. Click "Run workflow"
4. Select the environment (dev, staging, or prod)
5. Click "Run workflow" again

## Terraform Modules

### `terraform/modules/ai-service-accounts`

This module defines the service accounts for AI services. It:

- Creates service accounts for Vertex AI and Gemini
- Grants the necessary permissions
- Outputs the service account emails

Usage:

```hcl
module "ai_service_accounts" {
  source     = "./modules/ai-service-accounts"
  project_id = var.project_id
  env        = var.env
}
```

## Setup Process

The setup process consists of the following steps:

1. **Initial Setup**:
   - Create a GCP project
   - Enable required APIs
   - Create a master service account with owner permissions
   - Create a master service account key
   - Store the key in Secret Manager and GitHub secrets
   - Create a Terraform state bucket
   - Set up Workload Identity Federation

2. **Service Account Setup**:
   - Create service accounts for Vertex AI and Gemini
   - Grant the necessary permissions
   - Create service account keys
   - Store the keys in Secret Manager

3. **GitHub Secrets Setup**:
   - Update GitHub organization secrets with GCP service account keys
   - Update GitHub Codespaces secrets with GCP service account keys

4. **Verification**:
   - Verify that the GCP infrastructure is correctly set up
   - Verify that the GitHub secrets are correctly set
   - Verify that the Codespaces configuration is correctly set

## Security Considerations

1. **Service Account Keys**:
   - Service account keys are highly privileged and should be protected
   - Service account keys are stored in GitHub secrets and Secret Manager
   - Service account keys should be rotated regularly
   - Service account keys should be deleted from the filesystem after use

2. **Workload Identity Federation**:
   - Workload Identity Federation is more secure than service account keys
   - Workload Identity Federation should be used for GitHub Actions workflows
   - Workload Identity Federation should be configured with the principle of least privilege

3. **Secret Management**:
   - Secrets should be stored in Secret Manager
   - Secrets should be accessed using the principle of least privilege
   - Secrets should be rotated regularly

## Troubleshooting

### Common Issues

1. **Authentication Issues**:
   - Check that the service account key is correct
   - Check that the service account has the necessary permissions
   - Check that the Workload Identity Federation is correctly configured

2. **API Issues**:
   - Check that the required APIs are enabled
   - Check that the service account has the necessary permissions
   - Check that the API quotas are not exceeded

3. **GitHub Secrets Issues**:
   - Check that the GitHub token has the necessary permissions
   - Check that the GitHub organization exists
   - Check that the GitHub repository exists

### Debugging

1. **Verbose Logging**:
   - All scripts support verbose logging
   - Set the `DEBUG` environment variable to `true` to enable verbose logging
   - Example: `DEBUG=true ./scripts/verify_gcp_setup.sh`

2. **Manual Verification**:
   - Use the `gcloud` CLI to manually verify the setup
   - Use the GitHub CLI to manually verify the secrets
   - Use the Codespaces CLI to manually verify the secrets

## Conclusion

The infrastructure management system provides a comprehensive solution for managing the GCP infrastructure, GitHub secrets, and Codespaces configuration. It automates the setup and management of the infrastructure, making it easy to maintain and update.