# Orchestra Infrastructure Terraform Configuration

This directory contains the Terraform configuration for provisioning the Orchestra infrastructure in Google Cloud Platform.

## Components

- **Vertex AI Workbench**: 4 vCPUs, 16GB RAM for AI workloads
- **Firestore Database**: Native mode with multi-region in North America
- **Redis Instance**: 3GB cache for high-performance data access
- **Secret Manager**: Secure storage for sensitive information
- **Enabled APIs**: All required Google Cloud APIs

## Usage

### Prerequisites

Make sure you have:
- Terraform v1.0.0+ installed
- Google Cloud SDK installed and configured
- Service account with appropriate permissions

### Setup

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Plan the deployment:
   ```bash
   terraform plan -out=tfplan
   ```

3. Apply the configuration:
   ```bash
   terraform apply tfplan
   ```

**Note:** The `pgvector` extension for PostgreSQL needs to be enabled manually after the Cloud SQL instance is created. You can connect to the database using `gcloud sql connect [INSTANCE_NAME] --user=postgres` and run `CREATE EXTENSION IF NOT EXISTS vector;` in the `phidata_memory` database.

### Configuration Values

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Plan the deployment:
   ```bash
   terraform plan -out=tfplan
   ```

3. Apply the configuration:
   ```bash
   terraform apply tfplan
   ```

### Configuration Values

Edit the `terraform.tfvars` file to customize:
- GCP project ID
- Region and zone
- Environment name
- Figma PAT (Personal Access Token)

## Outputs

The `connection_details` output provides a JSON object with connection information for all provisioned resources.
