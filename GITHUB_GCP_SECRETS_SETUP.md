# GitHub GCP Secrets Setup Documentation

This document describes the GitHub secrets setup for GCP authentication in both GitHub Actions and Codespaces environments.

## Overview of Changes

The authentication method in GitHub Actions workflows has been temporarily changed from Workload Identity Federation (WIF) to service account key-based authentication for initial Terraform apply. This allows for easier initial setup and configuration of the infrastructure.

### Before: Workload Identity Federation
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ env.SERVICE_ACCOUNT }}
    create_credentials_file: true
```

### After: Service Account Key Authentication
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    # WIF configuration temporarily commented out for initial Terraform apply
    # workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
    # service_account: ${{ env.SERVICE_ACCOUNT }}
    credentials_json: ${{ secrets.GCP_PROJECT_ADMIN_KEY }}
    create_credentials_file: true
```

## GitHub Organization Secrets

The following secrets are set at the GitHub organization level (ai-cherry):

| Secret Name | Description | Used For |
|------------|-------------|----------|
| GCP_PROJECT_ID | The Google Cloud Project ID | Identifying the project in all GCP operations |
| GCP_PROJECT_NAME | The Google Cloud Project Name | Documentation and display purposes |
| GCP_PROJECT_ADMIN_KEY | Vertex AI admin service account key | Primary authentication for GitHub Actions workflows |
| GCP_VERTEX_AI_ADMIN_KEY | Same as PROJECT_ADMIN_KEY | Specific Vertex AI operations |
| GCP_SECRET_MANAGEMENT_KEY | Secret Management service account key | Managing GCP Secret Manager |
| GCP_GEMINI_API_KEY | Gemini API service account key | Authentication for Gemini API calls |
| GCP_GEMINI_CODE_ASSIST_KEY | Same as GEMINI_API_KEY | Specific for Gemini Code Assist |
| GCP_GEMINI_CLOUD_ASSIST_KEY | Same as GEMINI_API_KEY | Specific for Gemini Cloud Assist |

## GitHub Codespaces Environment Variables

The following environment variables are automatically set in GitHub Codespaces:

| Environment Variable | Source Secret | Description |
|---------------------|---------------|-------------|
| GCP_PROJECT_ID | GCP_PROJECT_ID | Project ID for GCP operations |
| GOOGLE_CLOUD_PROJECT | GCP_PROJECT_ID | Standard environment variable for GCP SDK |
| GCP_PROJECT_NAME | GCP_PROJECT_NAME | Project name for display purposes |
| GOOGLE_APPLICATION_CREDENTIALS | GCP_PROJECT_ADMIN_KEY | Standard GCP authentication credential path |
| VERTEX_AI_KEY | GCP_VERTEX_AI_ADMIN_KEY | Vertex AI authentication |
| GEMINI_API_KEY | GCP_GEMINI_API_KEY | Gemini API authentication |
| GEMINI_CODE_ASSIST_KEY | GCP_GEMINI_CODE_ASSIST_KEY | Gemini Code Assist authentication |
| GEMINI_CLOUD_ASSIST_KEY | GCP_GEMINI_CLOUD_ASSIST_KEY | Gemini Cloud Assist authentication |
| SECRET_MANAGER_KEY | GCP_SECRET_MANAGEMENT_KEY | Secret Manager authentication |

## Service Account Permissions

### Vertex AI Admin Service Account
This service account (`vertex-ai-admin@PROJECT_ID.iam.gserviceaccount.com`) has the following permissions:
- `roles/aiplatform.admin` - Full control over Vertex AI resources
- `roles/aiplatform.user` - Use Vertex AI resources
- `roles/aiplatform.serviceAgent` - Service agent role
- `roles/ml.admin` - Admin for ML Engine
- `roles/storage.admin` - Manage Cloud Storage for model artifacts
- `roles/artifactregistry.admin` - Manage Artifact Registry for models
- `roles/compute.admin` - Manage Compute Engine resources
- `roles/logging.admin` - Access to logging
- `roles/monitoring.admin` - Access to monitoring
- `roles/serviceusage.serviceUsageConsumer` - Service usage consumer for API activation

### Secret Management Service Account
This service account (`secret-management-admin@PROJECT_ID.iam.gserviceaccount.com`) has the following permissions:
- `roles/secretmanager.admin` - Secret Manager admin
- `roles/secretmanager.secretAccessor` - Access secrets
- `roles/secretmanager.secretVersionManager` - Manage secret versions
- `roles/iam.serviceAccountTokenCreator` - Create service account tokens
- `roles/iam.serviceAccountKeyAdmin` - Manage service account keys

### Gemini API Service Account
This service account (`gemini-api-admin@PROJECT_ID.iam.gserviceaccount.com`) has the following permissions:
- `roles/aiplatform.admin` - Full control over AI Platform resources (includes Gemini)
- `roles/aiplatform.user` - Use AI Platform resources
- `roles/serviceusage.serviceUsageConsumer` - Service usage consumer for API activation
- `roles/cloudkms.admin` - Key management for API keys
- `roles/secretmanager.admin` - Secret management for API keys
- `roles/iam.serviceAccountUser` - Service account user role
- `roles/storage.admin` - For model storage and data processing
- `roles/servicemanagement.admin` - Service management for API activation
- `roles/billing.projectManager` - Required to check and manage billing for API usage
- `roles/monitoring.admin` - For monitoring Gemini API usage and performance
- `roles/logging.admin` - For logging related to Gemini operations

## Maintenance and Updates

The following scripts are provided to manage and update these secrets:

### 1. Create Service Accounts and Update Secrets
This script creates the Vertex AI and Secret Management service accounts, generates keys, and updates the GitHub organization secrets.

```bash
./create_service_accounts_and_update_secrets.sh
```

### 2. Setup Gemini Access
This script creates the Gemini API service account, generates keys, and updates the GitHub organization secrets for Gemini-specific services.

```bash
./setup_gemini_access.sh
```

### 3. Update Codespaces Secrets
This script synchronizes the GitHub organization secrets with GitHub Codespaces environment variables.

```bash
./update_codespaces_secrets.sh
```

## Reversion to Workload Identity Federation

After initial setup and Terraform apply, you should consider reverting to Workload Identity Federation for more secure authentication. This involves:

1. Restoring the commented out WIF configuration in the GitHub Actions workflows
2. Removing the `credentials_json` parameter
3. Setting up the Workload Identity Federation provider in GCP if not already done

Example:
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ env.SERVICE_ACCOUNT }}
    create_credentials_file: true
```

## Security Considerations

1. Service account keys are stored as GitHub secrets, which are encrypted at rest
2. GitHub Actions has access to these secrets during workflow execution
3. GitHub Codespaces has access to these secrets during development
4. For maximum security, consider:
   - Regular rotation of service account keys
   - Limiting the permissions of service accounts to only what's necessary
   - Reversion to Workload Identity Federation after initial setup
   - Using separate service accounts for different purposes

## Troubleshooting

If you encounter authentication issues:

1. Verify the secrets exist in the GitHub organization settings
2. Check the service account permissions in GCP
3. Ensure the APIs are enabled for your GCP project
4. Run the appropriate script to regenerate keys and update secrets
