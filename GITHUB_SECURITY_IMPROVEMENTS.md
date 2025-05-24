# GitHub Security Improvements for AI Orchestra

This document outlines the security improvements made to the AI Orchestra project's GitHub integration, focusing on replacing hardcoded tokens with organization-level secrets and implementing best practices for GitHub Actions workflows.

## Overview of Changes

The following improvements have been implemented:

1. **Removed hardcoded GitHub tokens** from all scripts and replaced them with references to organization-level secrets
2. **Created a centralized GitHub authentication utility** (`github_auth.sh`) for consistent token management
3. **Updated deployment scripts** to use organization-level secrets for GCP authentication
4. **Created a GitHub Actions workflow template** that uses Workload Identity Federation (WIF) for secure GCP authentication
5. **Added verification tools** to ensure proper setup of GitHub organization secrets

## Updated Scripts

The following scripts have been updated to use organization-level secrets:

| Original Script                     | Updated Script                              | Description                                          |
| ----------------------------------- | ------------------------------------------- | ---------------------------------------------------- |
| `setup_github_secrets.sh`           | `setup_github_secrets.sh.updated`           | Sets up GitHub repository secrets for WIF            |
| `update_wif_secrets.sh`             | `update_wif_secrets.sh.updated`             | Updates GitHub repository secrets with WIF values    |
| `deploy_with_adc.sh`                | `deploy_with_adc.sh.updated`                | Deploys to GCP using Application Default Credentials |
| `configure_badass_keys_and_sync.sh` | `configure_badass_keys_and_sync.sh.updated` | Creates service accounts and syncs secrets           |
| `push_to_gcp.sh`                    | `push_to_gcp.sh.updated`                    | Pushes infrastructure to GCP                         |

## New Scripts and Templates

The following new scripts and templates have been created:

| Script/Template                            | Description                                   |
| ------------------------------------------ | --------------------------------------------- |
| `github_auth.sh.updated`                   | Centralized utility for GitHub authentication |
| `github-workflow-wif-template.yml.updated` | GitHub Actions workflow template using WIF    |
| `verify_github_secrets.sh`                 | Tool to verify GitHub organization secrets    |

## Required GitHub Organization Secrets

The following secrets should be set at the organization level:

| Secret Name                      | Description                                |
| -------------------------------- | ------------------------------------------ |
| `GH_CLASSIC_PAT_TOKEN`           | GitHub classic personal access token       |
| `GH_FINE_GRAINED_TOKEN`          | GitHub fine-grained personal access token  |
| `GCP_PROJECT_ID`                 | GCP project ID (e.g., "cherry-ai-project") |
| `GCP_REGION`                     | GCP region (e.g., "us-west4")              |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity Federation provider ID   |
| `GCP_SERVICE_ACCOUNT`            | Service account email for WIF              |

## How to Use the Updated Scripts

### 1. Set Up GitHub Organization Secrets

First, ensure that all required GitHub organization secrets are set up:

```bash
# Rename the updated script
mv setup_github_secrets.sh.updated setup_github_secrets.sh
chmod +x setup_github_secrets.sh

# Run the script to set up GitHub repository secrets
./setup_github_secrets.sh
```

### 2. Verify GitHub Organization Secrets

Use the verification tool to ensure all required secrets are available:

```bash
chmod +x verify_github_secrets.sh
./verify_github_secrets.sh
```

### 3. Use the Centralized GitHub Authentication Utility

When writing new scripts that need GitHub authentication, use the centralized utility:

```bash
# Rename the updated script
mv github_auth.sh.updated github_auth.sh
chmod +x github_auth.sh

# In your scripts, source the utility
source github_auth.sh

# Get a GitHub token
GITHUB_TOKEN=$(get_github_token)

# Authenticate with GitHub
authenticate_github "$GITHUB_TOKEN"
```

### 4. Use the GitHub Actions Workflow Template

When creating new GitHub Actions workflows, use the template as a starting point:

```bash
# Rename the updated template
mv github-workflow-wif-template.yml.updated .github/workflows/your-workflow-name.yml

# Edit the workflow file to customize it for your specific needs
```

## Best Practices for GitHub Security

1. **Never hardcode tokens** in scripts or configuration files
2. **Use organization-level secrets** for storing sensitive information
3. **Implement Workload Identity Federation** for GCP authentication instead of service account keys
4. **Rotate tokens regularly** to minimize the impact of potential leaks
5. **Use the principle of least privilege** when granting permissions to tokens and service accounts
6. **Enable secret scanning** in GitHub repositories to detect accidentally committed secrets
7. **Implement branch protection rules** to prevent direct pushes to main branches

## Transitioning to Workload Identity Federation

Workload Identity Federation (WIF) is a more secure alternative to service account keys for authenticating to GCP from GitHub Actions. The updated scripts and templates use WIF for authentication.

To set up WIF:

1. Run the `setup_github_secrets.sh` script to set up the required secrets
2. Use the `github-workflow-wif-template.yml` template for your GitHub Actions workflows
3. Verify that the WIF provider and service account are correctly configured

## Troubleshooting

If you encounter issues with the updated scripts:

1. Run the `verify_github_secrets.sh` script to check if all required secrets are available
2. Check the GitHub Actions workflow logs for authentication errors
3. Ensure that the service account has the necessary permissions in GCP
4. Verify that the Workload Identity Federation provider is correctly configured

For more information, refer to the [GitHub Actions documentation](https://docs.github.com/en/actions) and [Google Cloud Workload Identity Federation documentation](https://cloud.google.com/iam/docs/workload-identity-federation).
