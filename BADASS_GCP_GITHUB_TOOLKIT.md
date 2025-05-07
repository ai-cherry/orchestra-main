# Badass GCP & GitHub Integration Toolkit

## Overview

This toolkit provides a comprehensive solution for setting up "badass" service accounts with extensive permissions for Vertex AI and Gemini in Google Cloud Platform (GCP), and integrating them with GitHub for seamless CI/CD workflows. The toolkit is designed for the AI Orchestra project to enable powerful AI capabilities with minimal restrictions.

## Components

The toolkit consists of the following components:

1. **Terraform Configuration** (`terraform/vertex_gemini_setup.tf`)
   - Creates service accounts with extensive permissions
   - Sets up Workload Identity Federation for GitHub Actions
   - Configures IAM bindings and permissions

2. **Setup Script** (`apply_vertex_gemini_setup.sh`)
   - Applies the Terraform configuration
   - Creates service account keys
   - Stores keys in Secret Manager and GitHub secrets
   - Creates GitHub Actions workflow

3. **Documentation**
   - Setup Guide (`BADASS_VERTEX_GEMINI_SETUP.md`)
   - Code Examples (`VERTEX_GEMINI_CODE_EXAMPLES.md`)
   - Gemini Prompts (`gemini_gcp_github_prompts.md`)

4. **GitHub Actions Workflow** (`.github/workflows/deploy-to-gcp.yml`)
   - Authenticates with GCP using Workload Identity Federation
   - Deploys to Cloud Run

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  GitHub Actions │────▶│ Workload Identity│────▶│  GCP Service   │
│                 │     │   Federation    │     │   Accounts     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │                 │
                                               │  Vertex AI &    │
                                               │  Gemini APIs    │
                                               │                 │
                                               └─────────────────┘
```

## Service Accounts

### Vertex AI Service Account

The Vertex AI service account (`vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com`) has the following roles:

- `roles/aiplatform.admin`
- `roles/aiplatform.user`
- `roles/storage.admin`
- `roles/logging.admin`
- `roles/iam.serviceAccountUser`
- `roles/iam.serviceAccountTokenCreator`

This service account can perform any operation with Vertex AI, including:
- Creating and managing datasets
- Training and deploying models
- Running predictions
- Managing endpoints
- Accessing logs

### Gemini Service Account

The Gemini service account (`gemini-badass@cherry-ai-project.iam.gserviceaccount.com`) has the following roles:

- `roles/aiplatform.user`
- `roles/serviceusage.serviceUsageConsumer`
- `roles/iam.serviceAccountUser`
- `roles/iam.serviceAccountTokenCreator`

This service account can perform any operation with Gemini API, including:
- Generating text
- Creating multi-turn conversations
- Processing images
- Fine-tuning models

## Workload Identity Federation

Workload Identity Federation allows GitHub Actions workflows to authenticate with GCP without storing service account keys in GitHub secrets. The setup includes:

- A Workload Identity pool for GitHub Actions
- A provider for GitHub
- IAM bindings to allow GitHub Actions to impersonate the service accounts

## GitHub Secrets

The following secrets are stored in the GitHub organization:

- `VERTEX_SERVICE_ACCOUNT_KEY`: The key for the Vertex AI service account
- `GEMINI_SERVICE_ACCOUNT_KEY`: The key for the Gemini service account
- `WORKLOAD_IDENTITY_PROVIDER`: The Workload Identity provider for GitHub Actions

## Secret Manager

The following secrets are stored in Secret Manager:

- `vertex-ai-key`: The key for the Vertex AI service account
- `gemini-key`: The key for the Gemini service account

## GitHub Actions Workflow

The GitHub Actions workflow authenticates with GCP using Workload Identity Federation and deploys to Cloud Run. The workflow is triggered on pushes to the main branch and can also be triggered manually.

## Integration with AI Orchestra

This toolkit integrates with the AI Orchestra project by providing:

1. **Authentication**: Secure authentication with GCP using service accounts and Workload Identity Federation
2. **Permissions**: Extensive permissions for Vertex AI and Gemini APIs
3. **Deployment**: Automated deployment to Cloud Run using GitHub Actions
4. **Code Examples**: Python code examples for using Vertex AI and Gemini APIs

## Security Considerations

While this toolkit intentionally creates service accounts with extensive permissions for maximum flexibility, it's important to consider security implications:

1. **Principle of Least Privilege**: In a production environment, consider granting only the permissions that are necessary for your specific use case.
2. **Key Management**: Service account keys are sensitive and should be stored securely. The toolkit stores them in Secret Manager and GitHub secrets.
3. **Access Control**: Limit access to the service account keys and GitHub secrets to only those who need them.

## Getting Started

1. Make the setup script executable:
   ```bash
   chmod +x apply_vertex_gemini_setup.sh
   ```

2. Run the setup script:
   ```bash
   ./apply_vertex_gemini_setup.sh
   ```

3. Verify the setup by checking:
   - Service accounts in GCP
   - Secrets in Secret Manager
   - Secrets in GitHub
   - GitHub Actions workflow

4. Start using the service accounts with the code examples provided in `VERTEX_GEMINI_CODE_EXAMPLES.md`.

## Conclusion

This toolkit provides a comprehensive solution for setting up "badass" service accounts with extensive permissions for Vertex AI and Gemini in GCP, and integrating them with GitHub for seamless CI/CD workflows. It's designed to give you maximum flexibility and power for your AI Orchestra project.
