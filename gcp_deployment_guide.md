# Google Cloud Platform Deployment Guide

This guide provides instructions for setting up and deploying the Orchestra infrastructure on Google Cloud Platform. It covers Firestore, Redis (Memorystore), Secret Manager, and Cloud Run setup using Terraform.

## Prerequisites

Before you begin, ensure you have:

1. A Google Cloud Platform account with billing enabled
2. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
3. [Terraform](https://www.terraform.io/downloads.html) (version 1.0.0+) installed
4. Appropriate IAM permissions (Owner or Editor role on the project)
5. GitHub configured with appropriate secrets for CI/CD (if using GitHub Actions)

## Project Setup

### Initialize your GCP Project

If you haven't created a project yet:

```bash
# Set your project variables
export PROJECT_ID="orchestra-dev"  # Change to your preferred name
export PROJECT_NAME="Orchestra Development"
export BILLING_ACCOUNT="XXXXX-XXXXX-XXXXX"  # Your billing account ID

# Create the project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Link the project to your billing account
gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT
```

### Enable Required APIs

```bash
# Enable required services
gcloud services enable --project=$PROJECT_ID \
  firestore.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### Create Service Account for Terraform

```bash
# Create service account for Terraform
export SA_NAME="terraform-admin"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
  --project=$PROJECT_ID \
  --description="Terraform admin service account" \
  --display-name="Terraform Admin"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/owner"

# Create and download key (keep secure)
gcloud iam service-accounts keys create ./terraform-key.json \
  --project=$PROJECT_ID \
  --iam-account="${SA_EMAIL}"
```

## Terraform Setup

### Directory Structure

The Terraform configuration is organized as follows:

```
infra/
├── main.tf             # Main Terraform configuration
├── variables.tf        # Input variables declaration
├── outputs.tf          # Output values declaration
├── provider.tf         # Provider configuration
├── dev.tfvars          # Dev environment variables
├── modules/            # Reusable modules
│   ├── firestore/      # Firestore configuration
│   ├── redis/          # Redis (Memorystore) configuration
│   ├── secret-manager/ # Secret Manager configuration
│   └── cloud-run/      # Cloud Run configuration
└── init.sh             # Initialization script
```

### Initialize Terraform

```bash
cd infra

# Make init.sh executable
chmod +x init.sh

# Initialize Terraform with backend configuration
./init.sh
```

Alternatively, you can initialize manually:

```bash
# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/terraform-key.json"
export TF_VAR_project_id="$PROJECT_ID"

# Initialize Terraform
terraform init

# Create workspace for dev environment
terraform workspace new dev
```

## Deploy Infrastructure

### Review and Apply Terraform Configuration

```bash
# Select the 'dev' workspace
terraform workspace select dev

# Plan the changes
terraform plan -var-file=dev.tfvars -out=tfplan

# Apply the changes
terraform apply tfplan
```

### Key Resources Created

1. **Firestore** (Native mode)
   - Database with appropriate security rules
   - Collections for memory storage

2. **Redis** (Memorystore)
   - Redis instance for caching
   - Private VPC connection

3. **Secret Manager**
   - Secrets for API keys, credentials, and environment configuration
   - Secure access controls

4. **Cloud Run**
   - Service for running the API
   - Connection to VPC for Redis access

## Configuring the Backend

### Environment Variables

Set up environment variables for the backend to connect to Firestore and Redis:

```bash
# Export Terraform outputs
export FIRESTORE_PROJECT_ID=$(terraform output -raw firestore_project_id)
export REDIS_HOST=$(terraform output -raw redis_host)
export REDIS_PORT=$(terraform output -raw redis_port)
export SECRET_PREFIX=$(terraform output -raw secret_prefix)

# Create local .env file
cat > .env <<EOF
GOOGLE_CLOUD_PROJECT=$FIRESTORE_PROJECT_ID
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
SECRET_PREFIX=$SECRET_PREFIX
EOF
```

### Connecting to Firestore

The backend application can connect to Firestore using Application Default Credentials or a service account key:

```python
# Using Application Default Credentials (ADC)
from google.cloud import firestore
db = firestore.Client(project=PROJECT_ID)

# Using a service account key
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file('path/to/key.json')
db = firestore.Client(project=PROJECT_ID, credentials=credentials)
```

### Connecting to Redis

Redis connections can be made using the output variables from Terraform:

```python
import redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True)
```

## Integration Testing

### Running Integration Tests Locally Against Cloud Resources

To run integration tests against the deployed resources:

```bash
# Set environment variables
export RUN_INTEGRATION_TESTS=true
export RUN_FIRESTORE_TESTS=true
export GCP_PROJECT_ID=$(terraform output -raw firestore_project_id)

# If using service account key authentication
export GCP_SA_KEY_PATH="/path/to/service-account-key.json"

# Run tests
python -m pytest tests/integration/test_firestore_memory.py -v
```

### Verifying Firestore Connectivity

You can verify Firestore connectivity by running:

```bash
# Install google-cloud-firestore if not already installed
pip install google-cloud-firestore

# Run a simple connection test
python -c "
from google.cloud import firestore
db = firestore.Client(project='$FIRESTORE_PROJECT_ID')
print('Connected to Firestore in project:', db.project)
collection = db.collection('test_connection')
doc_ref = collection.document('test_doc')
doc_ref.set({'test': 'successful', 'timestamp': firestore.SERVER_TIMESTAMP})
print('Test document created successfully')
doc_ref.delete()
print('Test document cleaned up')
"
```

## Cloud Run Deployment

### Building and Deploying the API

```bash
# Build the Docker image
docker build -t gcr.io/$PROJECT_ID/orchestra-api:latest .

# Configure authentication
gcloud auth configure-docker

# Push the image
docker push gcr.io/$PROJECT_ID/orchestra-api:latest

# Deploy to Cloud Run
gcloud run deploy orchestra-api \
  --image gcr.io/$PROJECT_ID/orchestra-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$FIRESTORE_PROJECT_ID,REDIS_HOST=$REDIS_HOST,REDIS_PORT=$REDIS_PORT"
```

### Automating Deployment with Cloud Build

To set up continuous deployment with Cloud Build:

1. Create a `cloudbuild.yaml` file:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/orchestra-api:$COMMIT_SHA', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/orchestra-api:$COMMIT_SHA']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
    - 'run'
    - 'deploy'
    - 'orchestra-api'
    - '--image'
    - 'gcr.io/$PROJECT_ID/orchestra-api:$COMMIT_SHA'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--set-env-vars'
    - 'GOOGLE_CLOUD_PROJECT=$_FIRESTORE_PROJECT_ID,REDIS_HOST=$_REDIS_HOST,REDIS_PORT=$_REDIS_PORT'

images:
  - 'gcr.io/$PROJECT_ID/orchestra-api:$COMMIT_SHA'
```

2. Create a Cloud Build trigger:

```bash
gcloud builds triggers create github \
  --repo="github-org/orchestra-main" \
  --branch-pattern="main" \
  --build-config="cloudbuild.yaml" \
  --substitutions="_FIRESTORE_PROJECT_ID=$FIRESTORE_PROJECT_ID,_REDIS_HOST=$REDIS_HOST,_REDIS_PORT=$REDIS_PORT"
```

## Terraform Module Reference

### Firestore Module

The Firestore module creates a Firestore database in Native mode with appropriate location settings.

```hcl
module "firestore" {
  source     = "./modules/firestore"
  project_id = var.project_id
  location   = var.firestore_location
}
```

### Redis Module

The Redis module creates a Redis (Memorystore) instance with appropriate networking configuration.

```hcl
module "redis" {
  source     = "./modules/redis"
  project_id = var.project_id
  region     = var.region
  name       = "orchestra-cache"
  memory_size_gb = 1
}
```

### Secret Manager Module

The Secret Manager module creates secrets for storing sensitive data.

```hcl
module "secrets" {
  source     = "./modules/secret-manager"
  project_id = var.project_id
  secrets    = {
    "api-key" = "API key value",
    "db-password" = "Database password value"
  }
}
```

### Cloud Run Module

The Cloud Run module deploys the application to Cloud Run with appropriate configuration.

```hcl
module "cloud_run" {
  source     = "./modules/cloud-run"
  project_id = var.project_id
  region     = var.region
  name       = "orchestra-api"
  image      = "gcr.io/${var.project_id}/orchestra-api:latest"
  env_vars   = {
    "GOOGLE_CLOUD_PROJECT" = var.project_id,
    "REDIS_HOST" = module.redis.host,
    "REDIS_PORT" = module.redis.port
  }
}
```

## Troubleshooting

### Common Issues

1. **Permissions Issues**
   - Ensure the service account has the necessary roles
   - Verify Application Default Credentials are correctly set up

2. **Firestore Connectivity**
   - Check that the Firestore API is enabled
   - Verify project ID is correct
   - Ensure credentials have Firestore access

3. **Redis Connectivity**
   - Check VPC peering is correctly configured
   - Verify Redis host and port in environment variables
   - Check firewall rules to ensure access

4. **Cloud Run Deployment**
   - Verify Docker image builds correctly
   - Check environment variables are correctly set
   - Ensure service account has access to Firestore and Redis

### Getting Help

If you encounter issues not covered in this guide, refer to:

- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Terraform GCP Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
