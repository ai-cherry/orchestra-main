# AI Orchestra Configuration Management

This document describes the standardized configuration management approach for the AI Orchestra project.

## Overview

The AI Orchestra project uses a consistent approach to configuration management across all scripts and workflows. This approach:

1. Uses environment variables as the primary configuration mechanism
2. Provides sensible defaults for all configuration values
3. Allows overriding configuration via command-line arguments
4. Supports different environments (development, staging, production)

## Configuration Files

### `.env.template`

The `.env.template` file serves as a template for creating environment-specific configuration files. It includes all available configuration options with default values.

To create a new environment configuration:

```bash
cp .env.template .env.development  # For development environment
cp .env.template .env.staging      # For staging environment
cp .env.template .env.production   # For production environment
```

Then edit the file to set environment-specific values.

### `.env`

The `.env` file is the default configuration file used by scripts when no specific environment is specified. It should be created from `.env.template`:

```bash
cp .env.template .env
```

This file should not be committed to the repository, as it may contain sensitive information or developer-specific settings.

## Configuration Loading

### `load_env.sh`

The `load_env.sh` script provides functions for loading environment variables from `.env` files. It is used by other scripts to ensure consistent configuration loading.

Key functions:

- `load_env`: Loads environment variables from a specified file (defaults to `.env`)
- `get_config`: Gets a configuration value with a fallback default

Example usage in a script:

```bash
# Load environment variables
source "$(dirname "$0")/load_env.sh"

# Get configuration values with fallbacks
PROJECT_ID=$(get_config GCP_PROJECT_ID "cherry-ai-project")
REGION=$(get_config GCP_REGION "us-central1")
```

## Configuration Categories

### GCP Project Configuration

- `GCP_PROJECT_ID`: Google Cloud project ID
- `GCP_REGION`: Default Google Cloud region
- `GCP_ZONE`: Default Google Cloud zone
- `GCP_SERVICE_ACCOUNT`: Service account email

### Workload Identity Federation

- `GCP_WIF_PROVIDER`: Workload Identity Federation provider path

### Cloud Run Configuration

- `CLOUD_RUN_SERVICE_NAME`: Cloud Run service name
- `CLOUD_RUN_MIN_INSTANCES`: Minimum number of instances
- `CLOUD_RUN_MAX_INSTANCES`: Maximum number of instances
- `CLOUD_RUN_MEMORY`: Memory allocation
- `CLOUD_RUN_CPU`: CPU allocation
- `CLOUD_RUN_CONCURRENCY`: Request concurrency
- `CLOUD_RUN_TIMEOUT`: Request timeout
- `CLOUD_RUN_ALLOW_UNAUTHENTICATED`: Whether to allow unauthenticated access

### Artifact Registry Configuration

- `ARTIFACT_REGISTRY_REPO`: Artifact Registry repository name

### Cloud Workstation Configuration

- `WORKSTATION_CONFIG`: Cloud Workstation configuration name
- `WORKSTATION_NAME`: Cloud Workstation instance name
- `WORKSTATION_MACHINE_TYPE`: Machine type for Cloud Workstation

### Vertex AI Workbench Configuration

- `NOTEBOOK_NAME`: Vertex AI Workbench notebook name
- `NOTEBOOK_MACHINE_TYPE`: Machine type for Vertex AI Workbench

### Repository Configuration

- `REPO_URL`: GitHub repository URL
- `GITHUB_TOKEN`: GitHub personal access token for private repositories

### Environment Configuration

- `DEPLOYMENT_ENVIRONMENT`: Deployment environment (development, staging, production)

## GitHub Actions Integration

GitHub Actions workflows use the same configuration approach:

1. Default values are defined in the workflow file
2. Values can be overridden using GitHub variables and secrets
3. A `.env` file is created during workflow execution
4. Scripts use the `.env` file for configuration

Example workflow step:

```yaml
- name: Create .env file
  run: |
    cat > .env << EOF
    GCP_PROJECT_ID=${{ env.PROJECT_ID }}
    GCP_REGION=${{ env.REGION }}
    # Additional configuration...
    EOF
```

## Best Practices

1. **Never hardcode configuration values** in scripts or workflows
2. **Use environment variables** for all configuration
3. **Provide sensible defaults** for all configuration values
4. **Document all configuration options** in this file
5. **Keep sensitive information** in GitHub secrets or GCP Secret Manager
6. **Use different configurations** for different environments

## Migration Guide

If you have existing scripts that use hardcoded values:

1. Add the configuration options to `.env.template`
2. Update the script to use `load_env.sh` and `get_config`
3. Test the script with different configuration values
4. Update any GitHub Actions workflows to create a `.env` file

## Troubleshooting

If you encounter issues with configuration:

1. Check that `.env` file exists and contains the expected values
2. Verify that `load_env.sh` is being sourced correctly
3. Use `print_config` function to display current configuration values
4. Check for typos in environment variable names
