# GCP Complete Setup for AI Orchestra

This document explains how to use the `gcp_complete_setup.sh` script to set up the complete GCP environment for the AI Orchestra project.

## Overview

The `gcp_complete_setup.sh` script automates the following tasks:

1. Creating a service account key file
2. Installing the gcloud CLI
3. Setting up environment variables
4. Configuring gcloud
5. Setting up IDE syncing between Codespaces and GCP
6. Setting up GitHub Actions for CI/CD
7. Deploying to Cloud Run

This script is designed to work with the AI Orchestra project and uses hardcoded credentials to establish connections between Codespaces, GCP, and GitHub.

## Prerequisites

- Bash shell
- curl
- Git
- Docker (for local testing)

## Usage

To run the script, simply execute:

```bash
./gcp_complete_setup.sh
```

The script will:

1. Create a service account key file (`service-account-key.json`)
2. Install the gcloud CLI if it's not already installed
3. Set up environment variables in `.env` and `.bashrc`
4. Configure gcloud with the correct project, account, region, and zone
5. Set up IDE syncing between Codespaces and GCP
6. Set up GitHub Actions for CI/CD
7. Deploy the application to Cloud Run

## Configuration

The script uses the following hardcoded configuration:

- Project ID: `cherry-ai-project`
- Account: `scoobyjava@cherry-ai.me`
- Region: `us-central1`
- Zone: `us-central1-a`
- Service Name: `orchestra-api`
- Repository Name: `orchestra-main`

If you need to change any of these values, edit the script directly.

## Service Account Key

The script creates a mock service account key file for testing. In a production environment, you should replace this with a real service account key.

To create a real service account key:

1. Go to the GCP Console
2. Navigate to IAM & Admin > Service Accounts
3. Select or create a service account
4. Click on "Keys" > "Add Key" > "Create new key"
5. Select JSON as the key type
6. Click "Create"
7. Save the key file as `service-account-key.json` in the project directory

## IDE Syncing

The script sets up IDE syncing between Codespaces and GCP by:

1. Creating a configuration for the sync service
2. Creating a configuration for the VSCode extension

To use IDE syncing:

1. Install the "Google Cloud Code" extension in VSCode
2. Open the command palette (Ctrl+Shift+P)
3. Select "Cloud Code: Sign in to Google Cloud Platform"
4. Follow the prompts to sign in

## GitHub Actions

The script sets up GitHub Actions for CI/CD by creating a workflow file at `.github/workflows/deploy-to-cloud-run.yml`.

To use GitHub Actions:

1. Add your service account key as a secret named `GCP_SA_KEY` in your GitHub repository
2. Push your code to the `main` branch
3. GitHub Actions will automatically build and deploy your application to Cloud Run

## Deployment

The script deploys the application to Cloud Run by:

1. Building a container image
2. Pushing the image to Container Registry
3. Deploying the image to Cloud Run

If the gcloud CLI is not available, the script will provide instructions for manual deployment.

## Troubleshooting

### gcloud CLI Installation

If the gcloud CLI installation fails, you can install it manually:

```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### Authentication

If authentication fails, check that:

1. The service account key file is valid
2. The service account has the necessary permissions
3. The project ID is correct

### Deployment

If deployment fails, check that:

1. The Dockerfile is valid
2. The application code is correct
3. The service account has the necessary permissions

## Security Considerations

This script uses hardcoded credentials for simplicity. In a production environment, you should:

1. Use Workload Identity Federation instead of service account keys
2. Store sensitive configuration in Secret Manager
3. Implement key rotation
4. Use separate service accounts for different components
5. Apply the principle of least privilege

## Next Steps

After running the script, you should:

1. Verify that the application is deployed correctly
2. Set up monitoring and logging
3. Configure custom domains
4. Set up SSL certificates
5. Implement proper authentication and authorization