# GCP-GitHub Integration for AI Orchestra

This document outlines the secure integration between GitHub and Google Cloud Platform (GCP) for the AI Orchestra project, enabling seamless deployment, secret management, and infrastructure provisioning.

## Architecture Overview

The integration between GitHub and GCP consists of several key components:

1. **Secure Authentication Module** (`secure_auth.py`)
   - Handles authentication with both GCP and GitHub
   - Implements secure credential management
   - Supports multiple authentication methods including service account keys and Workload Identity Federation (WIF)

2. **Bidirectional Secret Synchronization** (`secure_secret_sync.py`)
   - Synchronizes secrets between GitHub and GCP Secret Manager
   - Handles versioning, conflict resolution, and audit logging
   - Supports different synchronization levels (organization, repository, environment)

3. **GitHub Actions Workflows** (`.github/workflows/`)
   - Provides templates for secure deployment to Cloud Run
   - Implements Workload Identity Federation for keyless authentication
   - Handles environment-specific configurations

4. **Integration Setup CLI** (`setup_gcp_github_integration.py`)
   - Unified command-line interface for the entire integration
   - Manages setup, synchronization, and verification processes
   - Provides step-by-step guidance for the integration

## Security Architecture

The integration follows security best practices:

- **Zero Persistent Credentials**: Uses Workload Identity Federation to eliminate the need for long-lived service account keys in GitHub
- **Secure Secret Management**: Implements bidirectional synchronization between GitHub Secrets and GCP Secret Manager
- **Least Privilege Access**: Service accounts and permissions follow the principle of least privilege
- **Secure Credential Handling**: Implements secure cleanup of temporary credential files
- **Audit Logging**: All operations are logged for compliance and troubleshooting

## Prerequisites

Before using this integration, you need:

1. **Google Cloud Platform**:
   - A GCP project with billing enabled
   - Owner or Editor permissions on the project
   - Enabled APIs: IAM, Secret Manager, Cloud Run, Artifact Registry

2. **GitHub**:
   - Organization or repository admin access
   - Personal Access Token (PAT) with appropriate permissions
   - GitHub Actions enabled

3. **Local Environment**:
   - Python 3.8+ with required packages
   - Google Cloud SDK (`gcloud`)
   - GitHub CLI (`gh`)

## Credentials Setup

The integration uses the following credentials:

| Credential | Description | Required Permissions |
|------------|-------------|---------------------|
| `GCP_MASTER_SERVICE_JSON` | Service account key with admin permissions | Editor/Owner on project |
| `GCP_SECRET_MANAGEMENT_KEY` | Service account for secret management | Secret Manager Admin |
| `GH_CLASSIC_PAT_TOKEN` | GitHub classic PAT | admin:org, repo, workflow |
| `GH_FINE_GRAINED_TOKEN` | GitHub fine-grained token | Repository contents R/W, Actions R/W |

## Getting Started

### Installation

Install the required dependencies:

```bash
pip install -r gcp_migration/requirements.txt
```

### Setting Up the Integration

1. **Initialize the integration**:

```bash
python gcp_migration/setup_gcp_github_integration.py setup \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry \
  --github-repo=ai-cherry/orchestra-main
```

2. **Sync secrets between GitHub and GCP**:

```bash
python gcp_migration/setup_gcp_github_integration.py sync-secrets \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry \
  --direction=bidirectional
```

3. **Verify the integration**:

```bash
python gcp_migration/setup_gcp_github_integration.py verify \
  --project-id=cherry-ai-project \
  --github-org=ai-cherry
```

## GitHub Actions Workflow Usage

Once the integration is set up, you can use the GitHub Actions workflow for deploying to Cloud Run:

1. Create a new workflow file in your repository at `.github/workflows/deploy.yml`
2. Copy the contents from the template at `gcp_migration/.github/workflows/deploy-cloud-run.yml`
3. Customize the workflow as needed for your specific service

The workflow will use Workload Identity Federation to authenticate with GCP, build and deploy your service to Cloud Run.

## Workload Identity Federation

### How It Works

Workload Identity Federation eliminates the need for storing service account keys in GitHub by establishing a trust relationship between GitHub Actions and GCP:

1. A Workload Identity Pool is created in GCP
2. A Workload Identity Provider is configured to trust GitHub's OIDC tokens
3. Service accounts are granted permissions to be impersonated by specific GitHub repositories
4. GitHub Actions uses the `google-github-actions/auth` action to obtain short-lived GCP credentials

### Benefits

- No long-lived credentials stored in GitHub
- Fine-grained control over which repositories can access which GCP resources
- Audit logs show exactly which GitHub workflow accessed GCP resources

## Secret Synchronization

### How It Works

The integration provides bidirectional secret synchronization between GitHub Secrets and GCP Secret Manager:

1. **GitHub to GCP**: Maps GitHub organization/repository secrets to GCP Secret Manager
2. **GCP to GitHub**: Updates GitHub secrets with values from GCP Secret Manager
3. **Bidirectional**: Ensures both systems are in sync

### Supported Levels

- **Organization**: Syncs organization-level secrets
- **Repository**: Syncs repository-level secrets
- **Environment**: Syncs environment-level secrets

## Command Reference

### Integration Setup CLI

```
python gcp_migration/setup_gcp_github_integration.py COMMAND [OPTIONS]
```

#### Commands:

- `setup`: Set up GCP-GitHub integration
- `sync-secrets`: Synchronize secrets between GitHub and GCP
- `verify`: Verify the GCP-GitHub integration setup
- `help`: Show help information

#### Setup Options:

- `--stage=STAGE`: Setup stage to execute (authentication, workload-identity, secret-sync, workflows, verification, all)
- `--project-id=ID`: GCP project ID
- `--region=REGION`: GCP region (default: us-central1)
- `--github-org=ORG`: GitHub organization name
- `--github-repo=REPO`: GitHub repository name (org/repo format)
- `--service-account=NAME`: Service account name (default: github-actions)
- `--pool-id=ID`: Workload identity pool ID (default: github-actions-pool)
- `--provider-id=ID`: Workload identity provider ID (default: github-actions-provider)
- `--wif-only`: Only set up Workload Identity Federation
- `--dry-run`: Don't actually make changes
- `--verbose`: Enable verbose logging

#### Sync Options:

- `--direction=DIRECTION`: Secret sync direction (github_to_gcp, gcp_to_github, bidirectional)
- `--level=LEVEL`: GitHub secret sync level (organization, repository, environment)

## Best Practices

1. **Use Workload Identity Federation**: Whenever possible, use WIF instead of service account keys

2. **Rotate Credentials Regularly**: For any service account keys in use, rotate them regularly

3. **Implement Least Privilege**:
   - Create dedicated service accounts for specific purposes
   - Grant only the permissions needed
   - Use condition-based IAM policies where appropriate

4. **Secure GitHub Repository**:
   - Enable branch protection rules
   - Require pull request reviews
   - Set up required status checks

5. **Environment-Specific Configurations**:
   - Use GitHub environments for staging/production
   - Set up required approvals for production deployments
   - Use environment-specific secrets

6. **Regular Verification**:
   - Run verification periodically to ensure integration is healthy
   - Review audit logs for unexpected access patterns

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Ensure GCP service account has required permissions
   - Verify GitHub token has required scopes
   - Check if service account keys are valid and not expired

2. **Workload Identity Issues**:
   - Verify pool and provider are correctly configured
   - Check IAM bindings for service accounts
   - Ensure GitHub Actions workflow is correctly configured

3. **Secret Synchronization Problems**:
   - Check audit logs for specific synchronization errors
   - Verify service account has Secret Manager Admin role
   - Ensure GitHub token has organization/repository admin access

### Logs and Diagnostics

- **Authentication Logs**: Check `gcp_auth.log` for authentication issues
- **Secret Sync Audit**: Review `secret_sync_audit.log` for synchronization details
- **GitHub Actions Logs**: View workflow run logs in GitHub Actions
- **GCP Audit Logs**: Check Cloud Audit Logs for API access details

## Security Considerations

1. **Environment Variables**:
   - Never hardcode credentials in scripts
   - Use environment variables or Secret Manager for sensitive values

2. **Service Account Keys**:
   - Treat service account keys like passwords
   - Store them securely when not using Workload Identity Federation
   - Implement proper key rotation procedures

3. **Secret Values**:
   - Be aware that secret values (not just names) are synchronized
   - Implement proper access controls for both GitHub and GCP secrets

4. **Logging and Monitoring**:
   - Set up alerts for suspicious activity
   - Regularly review audit logs
   - Monitor for unauthorized access attempts

## Resources

- [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-google-cloud-platform)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)