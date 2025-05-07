# Google Cloud Build Trigger Guide

This document outlines how to trigger Cloud Build pipelines defined in your `cloudbuild.yaml` file, both from GitHub and directly from the Google Cloud Console.

## Overview

The `cloudbuild.yaml` file defines a comprehensive CI/CD pipeline that:
- Runs linting and formatting checks
- Executes critical tests
- Performs Gemini code analysis
- Builds and pushes Docker images
- Scans for vulnerabilities
- Deploys to Cloud Run with secrets from Secret Manager

## Triggering from GitHub

### Setup GitHub Integration

1. **Connect your GitHub repository to Cloud Build**:
   - Go to the [Cloud Build Triggers page](https://console.cloud.google.com/cloud-build/triggers)
   - Click "Connect Repository"
   - Choose GitHub (Cloud Build GitHub App)
   - Follow the authorization flow
   - Select your repository

2. **Create a Build Trigger**:
   - Click "Create Trigger"
   - Name: `github-push-trigger`
   - Event: Choose "Push to a branch"
   - Source: Select your repository
   - Branch: `^main$` (or your preferred branch pattern)
   - Configuration: Choose "Cloud Build configuration file"
   - Location: Repository
   - Cloud Build configuration file location: `cloudbuild.yaml`
   - Click "Create"

3. **For Pull Request Validation** (optional):
   - Create a similar trigger but select "Pull Request" as the event
   - You might want a separate, more limited configuration file for PR builds

### Manually Trigger from GitHub

To manually trigger a build from a GitHub event:
- Push to your configured branch
- Create a PR (if you've set up PR triggers)
- Look for the Cloud Build status checks in your GitHub PR/commit

## Triggering from Google Cloud Console

### Manual Execution

1. **Start a build from the Cloud Console**:
   - Go to the [Cloud Build History page](https://console.cloud.google.com/cloud-build/builds)
   - Click "Build From Source" or "Trigger Build"
   - Select "Repository" as the source
   - Choose your repository and branch
   - Specify `cloudbuild.yaml` as the configuration file
   - Click "Run"

2. **Start a build with gcloud CLI**:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml --project=agi-baby-cherry
   ```

### Schedule Regular Builds

1. **Create a Cloud Scheduler job**:
   - Go to [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler)
   - Click "Create Job"
   - Set a schedule (cron format)
   - Target: HTTP
   - URL: `https://cloudbuild.googleapis.com/v1/projects/agi-baby-cherry/builds`
   - HTTP method: POST
   - Body:
     ```json
     {
       "source": {
         "repoSource": {
           "projectId": "agi-baby-cherry",
           "repoName": "YOUR_REPO_NAME",
           "branchName": "main"
         }
       },
       "steps": [
         {
           "name": "gcr.io/cloud-builders/gcloud",
           "args": ["builds", "submit", "--config", "cloudbuild.yaml"]
         }
       ]
     }
     ```
   - Auth header: Add appropriate service account authentication
   - Click "Create"

## Monitoring and Debugging Builds

- **View build logs**: Go to [Cloud Build History](https://console.cloud.google.com/cloud-build/builds)
- **Set up notifications**: Configure Cloud Build notifications on the Settings page
- **View artifacts**: Access build artifacts in the configured GCS bucket (`gs://agi-baby-cherry-cloudbuild-artifacts/`)

## Required Permissions

Ensure your service account (`vertex-agent@agi-baby-cherry.iam.gserviceaccount.com`) has the following roles:
- Cloud Build Service Account
- Secret Manager Secret Accessor
- Artifact Registry Writer
- Cloud Run Admin
- Vertex AI User

## Special Considerations

- **Secret Management**: The pipeline is configured to access secrets from Secret Manager. Ensure all required secrets exist.
- **Gemini Analysis**: The Gemini code analysis step requires access to Vertex AI. Check that the service account has the necessary permissions.
- **Artifact Storage**: Make sure the GCS bucket specified for artifacts exists.

## Troubleshooting

- **Build Timeouts**: If builds timeout, increase the `timeout` value in the `cloudbuild.yaml` file.
- **Missing Secrets**: Verify Secret Manager contains all required secrets.
- **Permission Issues**: Check service account permissions if you encounter access denied errors.
- **Docker Registry Access**: Ensure the service account has access to the Docker registry.
