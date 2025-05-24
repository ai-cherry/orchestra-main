# Gemini GCP Assistant

This document provides guidance on using Gemini Cloud in the GCP shell environment to help with GCP setup and testing via scripts.

## Overview

The `gemini_gcp_assistant.py` script provides a command-line interface to interact with Gemini Cloud for various GCP infrastructure management tasks, including:

- Generating Terraform configurations
- Analyzing and optimizing GCP resources
- Creating and testing deployment scripts
- Troubleshooting GCP issues
- Optimizing Terraform configurations
- Generating test scripts
- Setting up monitoring
- Creating backup scripts
- Setting up CI/CD pipelines

## Prerequisites

1. A GCP project with the Gemini API enabled
2. A Gemini API key
3. Python 3.6 or higher
4. The Google Cloud SDK installed and configured

## Setup

1. Make sure you have a Gemini API key. You can get one from the [Google AI Studio](https://makersuite.google.com/app/apikey).

2. Set the API key as an environment variable:

   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```

   Alternatively, you can create a `gemini.key` file in the root directory of the project:

   ```bash
   echo "your-api-key" > gemini.key
   ```

3. Make the script executable:
   ```bash
   chmod +x scripts/gemini_gcp_assistant.py
   ```

## Usage

The script can be used with various tasks. Here are some examples:

### Generate Terraform Configuration

```bash
./scripts/gemini_gcp_assistant.py --task generate_terraform --output terraform/generated/main.tf
```

This will generate a Terraform configuration for the AI Orchestra application and save it to `terraform/generated/main.tf`.

### Analyze GCP Resources

```bash
# First, export your current resources to a file
gcloud compute instances list --format=json > resources.json

# Then, analyze the resources
./scripts/gemini_gcp_assistant.py --task analyze_resources --input resources.json
```

This will analyze your GCP resources and provide recommendations for optimization.

### Create a Deployment Script

```bash
./scripts/gemini_gcp_assistant.py --task create_deployment_script --output scripts/deploy.sh
```

This will generate a deployment script for the AI Orchestra application and save it to `scripts/deploy.sh`.

### Troubleshoot GCP Issues

```bash
# First, save the error message to a file
echo "Error: Failed to create Cloud Run service: Permission denied" > error.txt

# Then, troubleshoot the issue
./scripts/gemini_gcp_assistant.py --task troubleshoot_issue --input error.txt
```

This will analyze the error message and provide a solution.

### Optimize Terraform Configuration

```bash
./scripts/gemini_gcp_assistant.py --task optimize_terraform --input terraform/main.tf
```

This will analyze your Terraform configuration and provide recommendations for improvement.

### Generate Test Script

```bash
# First, export your resources to a file
gcloud run services list --format=json > services.json

# Then, generate a test script
./scripts/gemini_gcp_assistant.py --task generate_test_script --input services.json --output scripts/test.sh
```

This will generate a test script for your Cloud Run services and save it to `scripts/test.sh`.

### Setup Monitoring

```bash
./scripts/gemini_gcp_assistant.py --task setup_monitoring --output monitoring/config.yaml
```

This will generate a monitoring configuration for the AI Orchestra application and save it to `monitoring/config.yaml`.

### Create Backup Script

```bash
./scripts/gemini_gcp_assistant.py --task create_backup_script --output scripts/backup.sh
```

This will generate a backup script for the AI Orchestra application and save it to `scripts/backup.sh`.

### Setup CI/CD

```bash
./scripts/gemini_gcp_assistant.py --task setup_ci_cd --output .github/workflows/ci-cd.yml
```

This will generate a GitHub Actions workflow for the AI Orchestra application and save it to `.github/workflows/ci-cd.yml`.

## Advanced Usage

### Customizing the Prompts

You can customize the prompts used for each task by editing the `TASK_PROMPTS` dictionary in the script.

### Using Different Models

You can specify a different Gemini model to use:

```bash
./scripts/gemini_gcp_assistant.py --task generate_terraform --model gemini-1.5-flash --output terraform/generated/main.tf
```

### Adjusting Temperature

You can adjust the temperature for generation:

```bash
./scripts/gemini_gcp_assistant.py --task generate_terraform --temperature 0.5 --output terraform/generated/main.tf
```

### Specifying Project Information

You can specify the GCP project ID, region, and environment:

```bash
./scripts/gemini_gcp_assistant.py --task generate_terraform --project-id my-project --region us-central1 --environment prod --output terraform/generated/main.tf
```

## Example Prompts for GCP Shell

Here are some example prompts you can use directly in the GCP Cloud Shell with Gemini Cloud Assist:

### 1. Generate Terraform for Cloud Run

```
Generate Terraform code for deploying a Cloud Run service with the following specifications:
- Service name: ai-orchestra-api
- Container image: gcr.io/cherry-ai-project/ai-orchestra-api:latest
- Memory: 2Gi
- CPU: 1
- Concurrency: 80
- Environment variables:
  - PROJECT_ID: cherry-ai-project
  - ENV: dev
  - REGION: us-central1
- Secret environment variables:
  - VERTEX_API_KEY from Secret Manager
  - GEMINI_API_KEY from Secret Manager
- Service account with appropriate permissions
- Public access
```

### 2. Analyze IAM Permissions

```
Analyze the following IAM permissions and suggest the least privilege permissions needed for a service account that will:
- Read from Firestore
- Write to Cloud Storage
- Call Vertex AI APIs
- Access Secret Manager secrets
```

### 3. Create a Deployment Script

```
Create a bash script that:
1. Builds a Docker image for a Python FastAPI application
2. Tags it with the current timestamp
3. Pushes it to Google Container Registry
4. Updates a Cloud Run service with the new image
5. Verifies the deployment was successful
6. Includes error handling and logging
```

### 4. Troubleshoot Cloud Run Issues

```
I'm getting the following error when deploying to Cloud Run:
"ERROR: (gcloud.run.deploy) PERMISSION_DENIED: The caller does not have permission"

What could be causing this and how do I fix it?
```

### 5. Optimize Terraform Configuration

```
Review this Terraform configuration for a Cloud Run service and suggest improvements for security, maintainability, and cost optimization:

resource "google_cloud_run_service" "default" {
  name     = "api"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/my-project/api:latest"
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
```

### 6. Generate a Test Script

```
Create a bash script that tests a Cloud Run API by:
1. Getting the URL of the service
2. Making HTTP requests to various endpoints
3. Validating the responses
4. Reporting success or failure
```

### 7. Setup Monitoring

```
Generate a Cloud Monitoring configuration that:
1. Creates alerts for Cloud Run service errors
2. Monitors CPU and memory usage
3. Tracks API latency
4. Sends notifications to a Slack channel
```

### 8. Create a Backup Strategy

```
Design a backup strategy for a Firestore database that:
1. Creates daily backups
2. Retains backups for 30 days
3. Stores backups in a separate region
4. Includes a verification step
```

### 9. Setup Workload Identity Federation

```
Provide step-by-step instructions to set up Workload Identity Federation for GitHub Actions to authenticate with GCP without using service account keys.
```

### 10. Optimize Cloud Run Configuration

```
Analyze this Cloud Run configuration and suggest optimizations for performance, cost, and security:

- Service: ai-orchestra-api
- Memory: 2Gi
- CPU: 2
- Min instances: 2
- Max instances: 10
- Concurrency: 80
- Timeout: 300s
```

## Conclusion

The Gemini GCP Assistant provides a powerful way to leverage Gemini's capabilities for GCP infrastructure management. By using the script or direct prompts in the GCP Cloud Shell, you can streamline your GCP setup and testing processes.
