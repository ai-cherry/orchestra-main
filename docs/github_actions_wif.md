# GitHub Actions with Workload Identity Federation

This document explains the GitHub Actions workflow for deploying the MCP server using Workload Identity Federation (WIF).

## Overview

The workflow (`wif-deploy.yml`) provides a straightforward deployment process:

1. **Test and Deploy**: The workflow tests the code before deployment to ensure quality.
2. **Environment-Specific Configurations**: Simple environment configurations are loaded from files in `config/environments/`.
3. **Secure Authentication**: Uses Workload Identity Federation for secure authentication with Google Cloud.
4. **Efficient Builds**: Leverages Docker Buildx for efficient image building and caching.

## Workflow Structure

### Test Job

The test job:

- Sets up Python and Poetry
- Caches Poetry dependencies
- Installs dependencies
- Runs tests with pytest

### Deploy Job

The deploy job:

- Only runs if tests pass
- Sets up Python and Poetry
- Installs dependencies
- Determines the environment (dev, staging, prod)
- Loads environment-specific configurations
- Authenticates to Google Cloud using Workload Identity Federation
- Builds and pushes the Docker image
- Deploys to Cloud Run with environment-specific settings
- Performs a simple health check

## Environment-Specific Configurations

Environment-specific configurations are stored in `config/environments/` as `.env` files:

- `dev.env`: Development environment configuration
- `staging.env`: Staging environment configuration
- `prod.env`: Production environment configuration

These files contain basic resource allocation settings for each environment.

## Workload Identity Federation

The workflow uses Workload Identity Federation for authentication with Google Cloud:

```yaml
- name: Google Auth via Workload Identity Federation
  id: auth
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
    token_format: "access_token"
```

This approach eliminates the need for storing service account keys in GitHub secrets, improving security.

## Required GitHub Secrets

The workflow requires the following GitHub secrets:

- `GCP_PROJECT_ID`: The Google Cloud project ID
- `GCP_REGION`: The Google Cloud region
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: The Workload Identity Provider resource name
- `GCP_SERVICE_ACCOUNT`: The service account email

## Deployment Process

1. Code is pushed to the main branch or workflow is manually triggered
2. Tests are run to ensure code quality
3. Environment is determined (dev, staging, prod)
4. Environment-specific configurations are loaded
5. Authentication to Google Cloud is performed using WIF
6. Docker image is built and pushed to Google Container Registry
7. Service is deployed to Cloud Run
8. Simple health check is performed

## Best Practices

1. **Keep Dependencies Updated**: Regularly update the GitHub Actions versions.
2. **Monitor Workflow Execution**: Check the GitHub Actions logs for any issues.
3. **Test Locally**: Test the deployment locally before pushing to GitHub.
4. **Secure Secrets**: Ensure that GitHub secrets are properly secured.
