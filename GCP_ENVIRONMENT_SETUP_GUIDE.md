# AI Orchestra GCP Environment Setup Guide

This guide provides detailed instructions for setting up the complete Google Cloud Platform (GCP) environment for the AI Orchestra project using Terraform and GitHub Codespaces.

## Overview

The AI Orchestra project uses the following GCP resources:

- **Service Accounts**: For Vertex AI, Gemini, and Cloud Run
- **IAM Permissions**: Proper access control for service accounts
- **Storage Buckets**: For model artifacts and data synchronization
- **Secret Manager**: For secure storage of API keys and credentials
- **Workload Identity Federation**: For GitHub Actions integration
- **Cloud Run**: For deploying the Orchestra API
- **Vertex AI**: For machine learning model training and deployment
- **Cloud Workstations**: For development environments

## Prerequisites

- Google Cloud Platform account with billing enabled
- Project ID: `cherry-ai-project` (Project Number: `525398941159`)
- GitHub repository with Codespaces enabled
- Service account with appropriate permissions:
  - Email: `orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com`
  - Roles: Editor, Compute Admin, Cloud SQL Admin, Vertex AI User, Workstations Admin

## Repository Structure

```
.
├── .env                      # Environment variables for local development
├── .env.example              # Template for environment variables
├── .github/                  # GitHub Actions workflows
├── packages/                 # Python packages
│   └── api/                  # FastAPI application
├── terraform/                # Terraform configuration
│   ├── gcp_setup.tf          # Main Terraform configuration
│   └── terraform.tfvars      # Terraform variables
├── apply_terraform.sh        # Script to apply Terraform configuration
├── run_local.sh              # Script to run the application locally
└── setup_gcp_environment.sh  # Script to set up the GCP environment
```

## Authentication

There are two ways to authenticate with GCP:

### 1. Using Service Account Key

Create a service account key file and use it for authentication:

```bash
# Set the GCP_MASTER_SERVICE_JSON environment variable
export GCP_MASTER_SERVICE_JSON='{"type":"service_account","project_id":"cherry-ai-project",...}'

# Or save it to a file
echo $GCP_MASTER_SERVICE_JSON > /tmp/gcp-credentials.json
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-credentials.json
```

### 2. Using GitHub Codespaces Secrets

Store the service account key as a GitHub Codespaces secret:

1. Go to GitHub → Settings → Codespaces → Repository secrets → New repository secret
2. Add your JSON key as `GCP_CREDENTIALS_JSON`

## Setting Up the GCP Environment

### Option 1: Using the Setup Script

The `setup_gcp_environment.sh` script automates the setup process:

```bash
# Make the script executable
chmod +x setup_gcp_environment.sh

# Run the script
./setup_gcp_environment.sh
```

This script will:
1. Initialize the GCP workspace using the service account
2. Set up the Python environment
3. Build a Docker image for the application
4. Deploy the application to Cloud Run (if gcloud is available)
5. Run the application locally

### Option 2: Using Terraform

The `apply_terraform.sh` script applies the Terraform configuration:

```bash
# Make the script executable
chmod +x apply_terraform.sh

# Run the script
./apply_terraform.sh
```

This script will:
1. Initialize Terraform
2. Plan Terraform changes
3. Apply Terraform changes
4. Show Terraform outputs
5. Clean up temporary files

### Terraform Configuration

The `terraform/gcp_setup.tf` file contains the Terraform configuration for the GCP environment:

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_path)
  project     = var.project_id
  region      = var.region
}

# Resources...
```

## Running the Application Locally

The `run_local.sh` script runs the application locally:

```bash
# Make the script executable
chmod +x run_local.sh

# Run the script
./run_local.sh
```

This script will:
1. Check if Poetry is installed
2. Install dependencies
3. Run the FastAPI application

## Continuous Integration and Deployment

### GitHub Actions Workflow

The GitHub Actions workflow automates the deployment process:

```yaml
name: Deploy to GCP

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: hashicorp/setup-terraform@v3
      
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_CREDENTIALS_JSON }}
      
      - name: Terraform Init
        run: terraform init
      
      - name: Terraform Apply
        run: terraform apply -auto-approve
```

### Workload Identity Federation

Workload Identity Federation allows GitHub Actions to authenticate with GCP without using service account keys:

```hcl
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}
```

## Syncing Development Environments

### GitHub Codespaces and GCP Cloud Workstations

To sync GitHub Codespaces with GCP Cloud Workstations:

1. **Version Control**:
   - Commit all code/configuration to GitHub
   - Sync repositories in Cloud Workstation environments

2. **Remote Development**:
   - Use VSCode Remote-SSH extension to connect to Cloud Workstation instances
   - Example SSH configuration:
     ```
     Host my-workstation
       HostName <workstation-ip>
       User dev-user
       IdentityFile ~/.ssh/google_cloud_private_key
     ```

3. **Terraform State Management**:
   - Store state remotely in GCP Storage buckets for team collaboration
   - Configure backend in Terraform:
     ```hcl
     terraform {
       backend "gcs" {
         bucket = "my-terraform-state-bucket"
         prefix = "terraform/state"
       }
     }
     ```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure the `GCP_MASTER_SERVICE_JSON` environment variable is set correctly
   - Verify the service account has the necessary permissions

2. **Terraform Errors**:
   - Run `terraform validate` to check for configuration errors
   - Run `terraform plan` to see what changes will be made

3. **Deployment Errors**:
   - Check the Cloud Run logs for error messages
   - Verify the Docker image was built correctly

## Resources

- [Google Cloud Platform Documentation](https://cloud.google.com/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)