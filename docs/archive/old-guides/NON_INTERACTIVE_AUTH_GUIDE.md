# Non-Interactive GCP Authentication

This guide explains how to set up and use non-interactive authentication for Google Cloud Platform (GCP) deployment in the AI Orchestra project.

## Overview

The AI Orchestra deployment process has been updated to eliminate the need for browser-based authentication prompts. This makes deployments more streamlined, especially in CI/CD environments or when running scripts in headless servers.

## Quick Start

```bash
# Run the setup script
./setup_service_account.sh

# Follow the instructions
# Once set up, all deployment scripts will use non-interactive authentication
```

## How It Works

The new authentication system uses a service account key file stored at `$HOME/.gcp/service-account.json`. All deployment scripts have been updated to check for this file and use it for authentication when available.

This approach provides several benefits:

1. No more browser-based authentication prompts
2. Consistent authentication across all scripts
3. Works with CI/CD systems and headless environments
4. Compatible with existing Workload Identity Federation in GitHub Actions

## Detailed Setup Process

### Option 1: Using the Setup Script (Recommended)

The `setup_service_account.sh` script walks you through the process:

1. Run the script:

   ```bash
   ./setup_service_account.sh
   ```

2. Follow the on-screen instructions to:
   - Create a new service account
   - Download and place the key file
   - Test authentication

### Option 2: Manual Setup

1. Create a service account with these roles:

   - Cloud Run Admin (`roles/run.admin`)
   - Artifact Registry Administrator (`roles/artifactregistry.admin`)
   - Service Account User (`roles/iam.serviceAccountUser`)

2. Create a key for the service account in JSON format

3. Place the key file at `$HOME/.gcp/service-account.json`

4. Set the environment variable:

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json
   ```

5. Add to your shell profile for persistence:
   ```bash
   echo 'export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.gcp/service-account.json' >> ~/.bashrc
   ```

### Option 3: Environment Variable Only

If you prefer not to store the key file on disk, you can export the entire key as an environment variable:

```bash
export GCP_MASTER_SERVICE_JSON='{ "type": "service_account", ... }'
```

## How Different Components Use Authentication

### 1. Local Deployment Scripts

Both `deploy.sh` and `deploy_anywhere.sh` have been updated to:

1. Check for the service account key file at `$HOME/.gcp/service-account.json`
2. Fall back to `GCP_MASTER_SERVICE_JSON` environment variable if the file doesn't exist
3. Only prompt for browser-based auth if neither is available

### 2. Docker Containers

The Dockerfile has been updated to:

1. Create an empty mount point for credentials at `/app/.gcp`
2. Accept credentials through volume mounting

When testing with `test_docker_build.sh`, the script will automatically mount your local credentials into the container if available.

### 3. GitHub Actions

The GitHub Actions workflow has been updated to:

1. Continue using Workload Identity Federation for production
2. Create the necessary directory structure to maintain compatibility

## Best Practices

1. **Do not commit service account keys to the repository**
2. Use different service accounts for different environments (dev/staging/prod)
3. Apply the principle of least privilege (only grant necessary permissions)
4. Regularly rotate service account keys

## Troubleshooting

### Common Issues

1. **Authentication fails despite key file being present**

   - Verify the key file is valid JSON: `jq . $HOME/.gcp/service-account.json`
   - Check if the service account has the necessary permissions
   - Ensure the service account is not disabled

2. **Deployment scripts still prompt for browser authentication**

   - Verify the environment variable is set: `echo $GOOGLE_APPLICATION_CREDENTIALS`
   - Check the path is correct
   - Ensure the GCP project ID in the deployment script matches the one in the service account

3. **Docker container can't authenticate**
   - Check that volume mounting is working: `docker inspect <container>`
   - Verify permissions on the key file

### Logs and Debugging

Both `deploy.sh` and `setup_service_account.sh` maintain logs that can help diagnose issues:

- `$HOME/setup_service_account.log`

## Reverting to Interactive Authentication

If you need to use browser-based authentication again:

```bash
# Remove the service account key file
rm $HOME/.gcp/service-account.json

# Unset the environment variable
unset GOOGLE_APPLICATION_CREDENTIALS
unset GCP_MASTER_SERVICE_JSON

# Authenticate with browser-based flow
gcloud auth login
```
