# Secure Credential Management for AI Orchestra

This document outlines the secure credential management architecture for the AI Orchestra project, including best practices, implementation details, and usage examples.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Security Best Practices](#security-best-practices)
- [Implementation Components](#implementation-components)
- [Usage Examples](#usage-examples)
- [Credential Rotation](#credential-rotation)
- [Troubleshooting](#troubleshooting)

## Overview

AI Orchestra requires secure access to various GCP services, including Vertex AI, Gemini, Firestore, and Redis. The secure credential management system provides a robust, scalable, and secure way to manage and access credentials across different environments.

Key features:

- Secret storage in Google Cloud Secret Manager
- Service account management with least privilege
- Workload Identity Federation for GitHub Actions
- Credential caching and automatic refresh
- Environment-specific credentials (dev, staging, prod)

## Architecture

The secure credential management architecture follows a multi-layered approach:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Access Layer   │     │  Secret Layer    │     │  Service Layer  │
│                 │     │                  │     │                 │
│ - GitHub Actions│────▶│ - Secret Manager │────▶│ - Vertex AI     │
│ - FastAPI App   │     │ - IAM            │     │ - Gemini        │
│ - CLI Scripts   │     │ - Key Rotation   │     │ - Firestore     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Components:

1. **Access Layer**: How applications and services authenticate to GCP

   - GitHub Actions: Uses Workload Identity Federation
   - FastAPI App: Uses service account keys or Workload Identity
   - CLI Scripts: Uses service account keys or user credentials

2. **Secret Layer**: How credentials are stored and managed

   - Secret Manager: Stores all credentials securely
   - IAM: Controls access to credentials
   - Key Rotation: Automatically rotates credentials

3. **Service Layer**: The GCP services being accessed
   - Vertex AI: For machine learning operations
   - Gemini: For generative AI capabilities
   - Firestore/Redis: For memory management

## Security Best Practices

The AI Orchestra credential management system follows these security best practices:

1. **Least Privilege Principle**

   - Each service account has only the permissions it needs
   - Separate service accounts for different components

2. **No Hardcoded Credentials**

   - All credentials are stored in Secret Manager
   - No credentials in code, config files, or environment variables

3. **Short-Lived Credentials**

   - Service account keys are rotated regularly
   - Workload Identity Federation provides short-lived tokens

4. **Defense in Depth**

   - Multiple layers of security controls
   - Audit logging for all credential access

5. **Secure Defaults**
   - All credentials are encrypted at rest and in transit
   - Automatic rotation of credentials

## Implementation Components

### 1. Bash Scripts

The `secure_credential_manager.sh` script provides CLI tools for managing credentials:

```bash
# Get a secret from Secret Manager
./secure_credential_manager.sh get-secret vertex-ai-key

# Create a new secret
./secure_credential_manager.sh create-secret api-key ./api-key.txt

# Rotate a service account key
./secure_credential_manager.sh rotate-key vertex-ai-agent@cherry-ai-project.iam.gserviceaccount.com

# Set up Workload Identity Federation
./secure_credential_manager.sh setup-wif

# Create a service account with specific roles
./secure_credential_manager.sh create-sa memory-system roles/firestore.user,roles/redis.editor
```

### 2. Python Library

The `core/security/credential_manager.py` module provides a Python interface for accessing credentials:

```python
from core.security.credential_manager import get_credential_manager

# Get a credential manager instance
credential_manager = get_credential_manager()

# Get a secret
api_key = credential_manager.get_secret("vertex-api-key")

# Get a service account key
sa_key = credential_manager.get_service_account_key("vertex-ai-agent")

# Get a JSON secret
config = credential_manager.get_json_secret("app-config")
```

### 3. FastAPI Dependencies

The `core/orchestrator/src/api/dependencies/credentials.py` module provides FastAPI dependencies for injecting credentials:

```python
from fastapi import Depends, FastAPI
from core.orchestrator.src.api.dependencies.credentials import get_vertex_ai_credentials

app = FastAPI()

@app.get("/vertex-info")
async def get_vertex_info(credentials: dict = Depends(get_vertex_ai_credentials)):
    # Use credentials to access Vertex AI
    return {"status": "authenticated"}
```

### 4. Terraform Module

The `terraform/modules/secure-credentials` module provides infrastructure-as-code for setting up the credential management system:

```hcl
module "secure_credentials" {
  source      = "./modules/secure-credentials"
  project_id  = var.project_id
  region      = var.region
  env         = var.env
  github_org  = "ai-cherry"
  github_repo = "orchestra-main"
}
```

## Usage Examples

### Example 1: Accessing Vertex AI from FastAPI

```python
from fastapi import Depends, FastAPI
from google.cloud import aiplatform
from core.orchestrator.src.api.dependencies.credentials import get_vertex_ai_credentials

app = FastAPI()

@app.post("/predict")
async def predict(
    request: PredictRequest,
    credentials: dict = Depends(get_vertex_ai_credentials)
):
    # Initialize Vertex AI with credentials
    aiplatform.init(
        project=credentials["project_id"],
        location="us-central1",
        credentials=credentials
    )

    # Use Vertex AI
    endpoint = aiplatform.Endpoint(request.endpoint_id)
    prediction = endpoint.predict(instances=request.instances)

    return {"prediction": prediction}
```

### Example 2: GitHub Actions Workflow

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write # Required for Workload Identity Federation

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      # Authenticate using Workload Identity Federation
      - id: "auth"
        name: "Authenticate to Google Cloud"
        uses: "google-github-actions/auth@v1"
        with:
          workload_identity_provider: "projects/525398941159/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
          service_account: "github-actions@cherry-ai-project.iam.gserviceaccount.com"

      # Deploy to Cloud Run
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: ai-orchestra
          region: us-central1
          image: gcr.io/cherry-ai-project/ai-orchestra:${{ github.sha }}
```

### Example 3: CLI Script

```bash
#!/bin/bash
# deploy_model.sh

# Get credentials from Secret Manager
export GOOGLE_APPLICATION_CREDENTIALS=$(mktemp)
./secure_credential_manager.sh get-secret vertex-ai-key > "$GOOGLE_APPLICATION_CREDENTIALS"
chmod 600 "$GOOGLE_APPLICATION_CREDENTIALS"

# Deploy model
gcloud ai models upload \
  --region=us-central1 \
  --display-name=my-model \
  --container-image-uri=gcr.io/cherry-ai-project/my-model:latest

# Clean up
rm -f "$GOOGLE_APPLICATION_CREDENTIALS"
```

## Credential Rotation

Credentials should be rotated regularly to minimize the risk of compromise. The AI Orchestra project implements automatic rotation for service account keys.

### Manual Rotation

To manually rotate a service account key:

```bash
./secure_credential_manager.sh rotate-key vertex-ai-agent@cherry-ai-project.iam.gserviceaccount.com
```

### Automatic Rotation

The project uses Cloud Scheduler and Cloud Functions to automatically rotate credentials:

1. A Cloud Scheduler job triggers a Cloud Function every 90 days
2. The Cloud Function rotates the service account key
3. The new key is stored in Secret Manager
4. Applications automatically pick up the new key on their next request

## Troubleshooting

### Common Issues

1. **Authentication Failures**

   If you encounter authentication failures:

   ```
   Error: Request had invalid authentication credentials
   ```

   Check:

   - Is GOOGLE_APPLICATION_CREDENTIALS set correctly?
   - Does the service account have the necessary permissions?
   - Has the key been rotated recently?

2. **Secret Not Found**

   If a secret is not found:

   ```
   Error: Secret not found: projects/cherry-ai-project/secrets/vertex-api-key
   ```

   Check:

   - Does the secret exist in Secret Manager?
   - Are you using the correct name and environment suffix?
   - Do you have permission to access the secret?

3. **Workload Identity Federation Issues**

   If GitHub Actions fails to authenticate:

   ```
   Error: Unable to get credential via Workload Identity Federation
   ```

   Check:

   - Is the Workload Identity Pool configured correctly?
   - Does the GitHub repository have the correct permissions?
   - Is the id-token permission set in the workflow?

### Getting Help

For additional help with credential management:

1. Check the logs in Cloud Logging
2. Review the IAM permissions for your service accounts
3. Verify Secret Manager access in the GCP Console
4. Contact the AI Orchestra security team

## Further Reading

- [Google Cloud Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
