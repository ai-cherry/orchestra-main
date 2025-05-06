# Workload Identity Federation for AI Orchestra

This document provides a comprehensive guide to the Workload Identity Federation (WIF) implementation for the AI Orchestra project. WIF enables secure authentication to Google Cloud Platform without using service account keys, improving security and simplifying credential management.

## Overview

Workload Identity Federation allows GitHub Actions workflows and Codespaces to authenticate to GCP using short-lived tokens instead of long-lived service account keys. This approach:

- Eliminates the need to store service account keys in GitHub secrets
- Reduces the risk of credential exposure
- Simplifies credential rotation
- Follows GCP security best practices

## Components

The WIF implementation consists of the following components:

1. **GCP Resources**:
   - Workload Identity Pool
   - Workload Identity Provider
   - Service Accounts with appropriate permissions
   - IAM bindings for WIF authentication

2. **GitHub Resources**:
   - Organization secrets for WIF configuration
   - Updated GitHub Actions workflows
   - Codespaces configuration

3. **Implementation Scripts**:
   - `orchestra_wif_master.sh`: Main setup script
   - `sync_github_gcp_secrets.sh`: Synchronizes GitHub and GCP secrets
   - `migrate_workflow_to_wif.sh`: Updates GitHub Actions workflows
   - `setup_wif_codespaces.sh`: Configures Codespaces for WIF

4. **Terraform Module**:
   - `terraform/modules/wif`: Infrastructure as Code for WIF setup

## Setup Instructions

### Prerequisites

- GCP project with billing enabled
- GitHub repository with GitHub Actions enabled
- GitHub organization admin access
- GCP project owner or editor permissions
- `gcloud` CLI installed
- `gh` CLI installed and authenticated

### Initial Setup

1. **Bootstrap with GCP_MASTER_SERVICE_JSON**:

   ```bash
   # Set environment variables
   export GCP_MASTER_SERVICE_JSON='<your-service-account-key-json>'
   export GITHUB_TOKEN='<your-github-pat>'
   
   # Run the master setup script
   ./orchestra_wif_master.sh
   ```

2. **Migrate GitHub Actions Workflows**:

   ```bash
   # Update all workflows to use WIF
   ./migrate_workflow_to_wif.sh
   ```

3. **Configure Codespaces**:

   ```bash
   # Set up Codespaces for WIF authentication
   ./setup_wif_codespaces.sh
   ```

### Using Terraform

Alternatively, you can use Terraform to set up the WIF infrastructure:

```bash
# Initialize Terraform
cd terraform
terraform init

# Apply the configuration
terraform apply -var="project_id=cherry-ai-project" -var="github_org=ai-cherry" -var="github_repo=orchestra-main"
```

## GitHub Actions Workflow Example

Here's an example of a GitHub Actions workflow using WIF authentication:

```yaml
name: Deploy with WIF

on:
  push:
    branches: [ main ]

permissions:
  contents: read
  id-token: write  # Required for requesting the JWT

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER_ID }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
      
      # Deployment steps
      # ...
```

## Codespaces Integration

For Codespaces, the WIF authentication is set up automatically when you open the repository in Codespaces. The `setup_wif_codespaces.sh` script is executed as part of the Codespaces initialization process.

To manually refresh the authentication:

```bash
# Refresh the GitHub token for WIF authentication
refresh-wif-token
```

## Secret Management

The WIF implementation includes bidirectional synchronization between GitHub organization secrets and GCP Secret Manager. This ensures that secrets are consistently available in both environments.

To manually synchronize secrets:

```bash
# Synchronize GitHub and GCP secrets
./sync_github_gcp_secrets.sh
```

## Service Accounts

The following service accounts are configured for WIF:

| Service Account | Purpose | Roles |
|-----------------|---------|-------|
| orchestrator-api | Cloud Run API service | roles/run.admin, roles/secretmanager.secretAccessor, roles/firestore.user |
| phidata-agent-ui | Cloud Run UI service | roles/run.admin, roles/secretmanager.secretAccessor |
| github-actions | GitHub Actions workflows | roles/artifactregistry.writer, roles/run.admin, roles/secretmanager.secretAccessor, roles/storage.admin |
| codespaces-dev | Codespaces development | roles/viewer, roles/secretmanager.secretAccessor, roles/logging.viewer |

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Check that the WIF provider and service account secrets are correctly set in GitHub
   - Verify that the service account has the necessary permissions
   - Ensure the repository is correctly configured in the WIF provider

2. **Missing Secrets**:
   - Run `sync_github_gcp_secrets.sh` to synchronize secrets
   - Check that the service account has access to Secret Manager

3. **Codespaces Authentication Issues**:
   - Run `refresh-wif-token` to refresh the GitHub token
   - Check that the GITHUB_TOKEN environment variable is set
   - Verify that the service account has the necessary permissions

### Logs and Debugging

- Check GitHub Actions workflow logs for authentication errors
- Use `gcloud auth list` to verify authentication status
- Check GCP audit logs for permission issues

## Security Considerations

While WIF is more secure than service account keys, it's important to follow these best practices:

1. Regularly review and audit IAM permissions
2. Limit service account permissions to the minimum required
3. Use repository and branch conditions in WIF provider configuration
4. Rotate the bootstrap GCP_MASTER_SERVICE_JSON key regularly

## Maintenance

### Regular Maintenance Tasks

1. **Audit IAM Permissions**:
   - Regularly review service account permissions
   - Remove unnecessary permissions

2. **Update WIF Configuration**:
   - Update the WIF provider configuration when repository structure changes
   - Add new service accounts as needed

3. **Rotate Bootstrap Key**:
   - Rotate the GCP_MASTER_SERVICE_JSON key annually
   - Update the key in GitHub secrets

## References

- [Google Cloud Workload Identity Federation Documentation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions Authentication to Google Cloud](https://github.com/google-github-actions/auth)
- [Terraform Google Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)