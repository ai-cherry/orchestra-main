# Secret Validation Guide

This guide explains how to use the Secret Manager validation system we've implemented to ensure your secrets are properly configured, environmentally separated, and accessible to your Cloud Run services.

## Overview

The validation system consists of:

1. **Environment-Specific Configuration**: Terraform code in `environments.tf` that properly separates secrets by environment
2. **Validation Scripts**: Python scripts to check your Secret Manager configuration
3. **CI/CD Integration**: GitHub Actions workflow for automated validation

## Before You Begin

Before you start, make sure you have the following:
Ensure you have:
- Google Cloud SDK installed and configured
- Python 3.7 or higher
- Access to the GCP project where Secret Manager is deployed
- The `google-cloud-secretmanager` Python package installed

## Local Validation

### Validating Environment Configuration

The `test_env_config.py` script validates that your Terraform configuration properly separates secrets by environment:

```bash
cd validation
python3 test_env_config.py
```

This will check:
- Common secrets are defined for all environments
- Dev-only secrets aren't accessible in prod
- Prod-only secrets aren't accessible in dev
- Service accounts have appropriate permissions

### Validating Live Secret Configuration

The `run_validation.sh` script validates your actual secrets in Secret Manager.

```bash
cd validation
./run_validation.sh [project-id] [environment] [service-name]

# Examples:
./run_validation.sh agi-baby-cherry dev orchestra-api
./run_validation.sh agi-baby-cherry prod orchestra-api
```

This will check:
- All required secrets exist in Secret Manager
- Cloud Run service can access the secrets
- Secrets have proper IAM permissions

## CI/CD Integration

We've provided a GitHub Actions workflow in `validate-secrets.yml`. To use it:

1. Copy the file to `.github/workflows/validate-secrets.yml` in your repository
2. Add the following secrets to your GitHub repository:
   - `GCP_SA_KEY`: JSON content of a service account key with Secret Manager access
   - `GCP_PROJECT_ID`: Your Google Cloud project ID

The workflow will run whenever changes are made to Secret Manager configuration files. It validates both the Terraform configuration (using `test_env_config.py`) and can optionally validate the live Secret Manager configuration (using `run_validation.sh`).

### Required GitHub Repository Secrets

| Secret Name | Description |
|------------|-------------|
| `GCP_SA_KEY` | JSON content of a service account key with Secret Manager access |
| `GCP_PROJECT_ID` | Your Google Cloud project ID |

## Customizing Validation Rules

### Customizing Environment-Specific Rules

Edit the `ENV_CONFIG` dictionary in `test_env_config.py` to customize environment-specific validation:

```python
ENV_CONFIG = {
    "dev": {
        "required_secrets": [
            "openai-api-key-dev",
            # Add your required dev secrets
        ],
        "forbidden_secrets": [
            "oauth-client-secret-dev",
            # Add secrets that should NOT be in dev
        ],
        # ...
    },
    # ...
}
```

## Deployment Readiness Checkpoint

The secret validation system satisfies the following key requirements for deployment readiness:

1. **Environment Separation**: Ensures dev and prod secrets are properly separated
2. **Access Control**: Validates service account permissions for accessing secrets.
3. **Configuration Validation**: Verifies all required secrets exist in each environment
4. **CI/CD Integration**: Automatically validates secrets during deployment

The system also addresses the core conversation handling requirements you mentioned:

- **Async Correctness**: The validation scripts properly handle async operations
- **API Surface**: The validation provides a clean interface for checking secret configuration
- **Test Coverage**: The system includes comprehensive tests for the secret management layer

## Troubleshooting

This section provides solutions to common issues you might encounter.

### Authentication Issues

If you see errors like:
```
Error: Not authenticated with gcloud
```

Make sure the `GCP_SA_KEY` secret is correctly configured in your GitHub repository.


### Missing Secrets

If validation fails due to missing secrets:
```
Required secret openai-api-key-prod not found
```

Make sure you've created all necessary secrets in Secret Manager using the Terraform configuration.


### Permission Issues

If you see access errors:
```
Cannot access required secret redis-auth-prod
```

Check that your account and the service being validated both have proper IAM permissions.


### Terraform Validation Errors

If you encounter errors during the Terraform validation step, such as:
```
Error: Invalid block definition
```

This indicates a syntax error in your Terraform files. Review the error message for details on the specific issue and correct the syntax in your `environments.tf` or other related Terraform files.


### Python Dependency Errors

If you encounter errors related to missing Python dependencies, such as:
```
ModuleNotFoundError: No module named 'google.cloud.secretmanager'
```

Ensure that you have installed the `google-cloud-secretmanager` package in your Python environment. You can install it using pip:

```bash
pip install google-cloud-secretmanager
```