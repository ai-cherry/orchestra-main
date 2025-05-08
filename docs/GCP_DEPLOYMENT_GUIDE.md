# AI Orchestra GCP Deployment Guide

This guide provides comprehensive instructions for deploying the AI Orchestra project to Google Cloud Platform (GCP) using GitHub Actions and GitHub Codespaces.

## Table of Contents

1. [Setup Overview](#setup-overview)
2. [GitHub Actions Workflow](#github-actions-workflow)
3. [Dev Container Configuration](#dev-container-configuration)
4. [Deployment Steps](#deployment-steps)
5. [Monitoring and Verification](#monitoring-and-verification)
6. [Customization Options](#customization-options)
7. [Troubleshooting](#troubleshooting)

## Setup Overview

The AI Orchestra project uses two main components for GCP deployment:

1. **GitHub Actions Workflow**: Automates the build, test, and deployment process to GCP Cloud Run
2. **Dev Container Configuration**: Sets up a consistent development environment with GCP authentication

Both components use Workload Identity Federation for secure authentication to GCP without storing service account keys in GitHub.

## GitHub Actions Workflow

The workflow file (`.github/workflows/deploy-to-gcp.yml`) handles the CI/CD pipeline:

- Triggers on any push to the repository
- Uses Workload Identity Federation for secure GCP authentication
- Sets up Python 3.11 and Poetry 1.7.1
- Runs tests before deployment
- Builds and pushes a Docker container to Google Container Registry (GCR)
- Deploys to Cloud Run with appropriate configuration

## Dev Container Configuration

The Dev Container configuration (`.devcontainer/devcontainer.json`) provides a consistent development environment:

- Installs Python 3.11, Poetry 1.7.1, and Google Cloud CLI
- Configures GCP authentication using the `GCP_SERVICE_ACCOUNT_KEY` secret
- Sets environment variables for GCP tools
- Installs necessary VS Code extensions

## Deployment Steps

### 1. Trigger the GitHub Actions Workflow

The `deploy-to-gcp.yml` workflow is configured to trigger on any push to the repository. To initiate the deployment:

#### Option 1: Automatic Trigger
Make a small change to your codebase (e.g., update a comment or configuration file) and push it:

```bash
git add .
git commit -m "Trigger deployment to GCP"
git push
```

#### Option 2: Manual Trigger
You can also manually trigger the workflow from the GitHub Actions tab in your repository.

### 2. Monitor the Deployment

Once the workflow is triggered:

1. Go to the **Actions** tab in your GitHub repository
2. Select the running instance of the **Deploy to GCP** workflow
3. Expand the logs for each step to monitor progress:
   - Checkout code
   - Set up Python and Poetry
   - Install dependencies
   - Run tests
   - Authenticate to Google Cloud
   - Build and push container
   - Deploy to Cloud Run

Look for any errors, especially in the authentication or deployment stages.

### 3. Verify the Deployed Service

After the workflow completes successfully:

#### Get the Service URL
The workflow deploys your application to Cloud Run, and the output includes a URL (e.g., `https://orchestra-api-XXXXX-uc.a.run.app`).

Check the workflow logs for the exact URL in the "Deploy to Cloud Run" step or the "Show Output" step.

#### Test the Service
Open the URL in a browser or use a tool like curl to test the endpoints:

```bash
curl https://orchestra-api-XXXXX-uc.a.run.app
```

#### Check Cloud Run Console
1. Log in to the Google Cloud Console
2. Navigate to Cloud Run and select your service (e.g., `orchestra-api`)
3. Confirm the service is running and check its status

#### CLI Verification
From your Codespace or local machine with gcloud installed, run:

```bash
gcloud run services describe orchestra-api --region us-central1
```

This will display details about your deployed service, including its status and URL.

## Customization Options

### Modify the Service Name
Edit the `SERVICE_NAME` variable in `.github/workflows/deploy-to-gcp.yml` if you want a different service name on Cloud Run.

### Adjust Resources
Update the memory and CPU settings in the workflow's "Deploy to Cloud Run" step:

```yaml
memory: 1Gi  # Increase from 512Mi if needed
cpu: 2       # Increase from 1 if needed
```

### Add Environment Variables
In the workflow file, add environment variables under the env_vars section of the "Deploy to Cloud Run" step:

```yaml
env_vars: |
  PROJECT_ID=${{ env.PROJECT_ID }}
  REGION=${{ env.REGION }}
  ENVIRONMENT=prod
  KEY1=value1
  KEY2=value2
```

Replace `KEY1=value1,KEY2=value2` with your application-specific variables.

### Configure Scaling
Add scaling parameters to the "Deploy to Cloud Run" step:

```yaml
min_instances: 1
max_instances: 10
```

## Troubleshooting

### Authentication Errors
- Ensure your Workload Identity Federation is correctly set up
- Verify the service account has the necessary permissions:
  - `roles/run.admin`
  - `roles/storage.admin`
  - `roles/iam.serviceAccountUser`

### Build Failures
- Check the Docker build logs in the workflow for errors in your Dockerfile or dependencies
- Verify that Poetry is correctly configured in your project

### Deployment Failures
- Verify the Cloud Run region and service configuration match your GCP setup
- Check if the service account has the necessary permissions to deploy to Cloud Run

### Dev Container Issues
- If the Dev Container fails to authenticate with GCP, check the `GCP_SERVICE_ACCOUNT_KEY` secret
- Run the verification script manually: `.devcontainer/setup_and_verify.sh`

### Logs
- Detailed logs are available in the GitHub Actions output
- Cloud Run logs can be viewed in the Cloud Run console under the "Logs" tab
- Dev Container logs are stored in `/workspaces/orchestra-main/codespace_setup.log`

## GitHub Codespaces Setup

### Rebuild Your Codespace

1. Open your Codespace in GitHub (or start a new one if it's not already running)
2. Open the Command Palette:
   - Windows/Linux: `Ctrl+Shift+P`
   - Mac: `Cmd+Shift+P`
3. Select **Codespaces: Rebuild Container**
4. Wait for the rebuild to complete. During this process, the `postCreateCommand` will run, authenticating your Codespace with GCP automatically.

### Verify Authentication

Once the Codespace rebuilds, open the terminal and run these commands to confirm everything is set up correctly:

```bash
# Check authenticated accounts
gcloud auth list

# Check the active project
gcloud config get-value project
```

If the service account is listed and active (marked with *), and the project ID matches `cherry-ai-project`, the setup is complete.