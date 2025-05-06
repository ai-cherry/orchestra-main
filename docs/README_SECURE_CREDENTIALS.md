# AI Orchestra Secure Credential Management System

This document provides an overview of the secure credential management system implemented for the AI Orchestra project, including instructions for setup, usage, and maintenance.

## Table of Contents

- [Overview](#overview)
- [Components](#components)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage-guide)
- [Maintenance](#maintenance)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The AI Orchestra secure credential management system provides a robust, scalable, and secure way to manage credentials across different environments and components. It addresses the security vulnerability found in `track_migration_progress.sh` and establishes a comprehensive credential management architecture.

Key features:
- Secure storage of credentials in Google Cloud Secret Manager
- Service account management with least privilege
- Workload Identity Federation for GitHub Actions
- Automatic credential rotation
- Environment-specific credentials (dev, staging, prod)
- Integration with FastAPI, Python code, and bash scripts

## Components

The system consists of the following components:

### 1. Bash Scripts

- `secure_credential_manager.sh`: CLI tool for credential management
  - Get secrets from Secret Manager
  - Create and update secrets
  - Rotate service account keys
  - Set up Workload Identity Federation

- `implementation_plan.sh`: Script for deploying the infrastructure
  - Deploy Terraform infrastructure
  - Set up Workload Identity Federation
  - Migrate existing credentials
  - Update application code
  - Sync GitHub and GCP secrets
  - Set up automatic credential rotation

### 2. Python Modules

- `core/security/credential_manager.py`: Python interface for credential management
  - Access secrets from Secret Manager
  - Cache credentials for performance
  - Handle credential rotation
  - Support for different environments

- `core/orchestrator/src/api/dependencies/credentials.py`: FastAPI dependencies
  - Inject credentials into API routes
  - Provide specialized dependencies for different services
  - Support for async operations

### 3. Infrastructure as Code

- `terraform/modules/secure-credentials/main.tf`: Terraform module
  - Service account creation
  - Secret Manager resources
  - Workload Identity Federation configuration
  - IAM permissions

### 4. GitHub Actions

- `.github/workflows/secure-deployment.yml`: GitHub Actions workflow
  - Uses Workload Identity Federation for authentication
  - Securely accesses credentials
  - Deploys to Cloud Run

### 5. Documentation

- `docs/SECURE_CREDENTIAL_MANAGEMENT.md`: Architecture and best practices
- `docs/CREDENTIAL_INTEGRATION_GUIDE.md`: Developer integration guide
- `docs/CREDENTIAL_IMPLEMENTATION_CHECKLIST.md`: Implementation verification

### 6. Examples and Tests

- `examples/credential_management_example.py`: Example usage
- `test_credential_system.py`: Test script

## Setup Instructions

Follow these steps to set up the secure credential management system:

### Prerequisites

- Google Cloud SDK installed and configured
- Terraform installed
- GitHub CLI installed
- Python 3.11+ installed
- Poetry installed

### 1. Deploy the Infrastructure

Run the implementation plan script:

```bash
# Make the script executable
chmod +x implementation_plan.sh

# Run the script
./implementation_plan.sh
```

Select option 7 to run all steps, or run individual steps as needed.

### 2. Install Dependencies

Install the required Python dependencies:

```bash
# Using Poetry
poetry add google-cloud-secret-manager google-cloud-iam redis cryptography

# Or using pip
pip install google-cloud-secret-manager google-cloud-iam redis cryptography
```

### 3. Set Up Environment Variables

Set the required environment variables:

```bash
# Set the GCP project ID
export GCP_PROJECT_ID="cherry-ai-project"

# Set the environment (dev, staging, prod)
export ENVIRONMENT="dev"

# Set the credentials path (if not using Workload Identity Federation)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 4. Verify the Setup

Run the test script to verify the setup:

```bash
# Make the script executable
chmod +x test_credential_system.py

# Run the test script
./test_credential_system.py
```

## Usage Guide

### Using the Bash Script

```bash
# Get a secret
./secure_credential_manager.sh get-secret secret-name

# Create a secret
./secure_credential_manager.sh create-secret secret-name /path/to/secret-file

# Rotate a service account key
./secure_credential_manager.sh rotate-key service-account@project-id.iam.gserviceaccount.com

# Set up Workload Identity Federation
./secure_credential_manager.sh setup-wif

# Create a service account with specific roles
./secure_credential_manager.sh create-sa sa-name roles/role1,roles/role2
```

### Using the Python Module

```python
from core.security.credential_manager import get_credential_manager

# Get the credential manager
credential_manager = get_credential_manager()

# Get a secret
api_key = credential_manager.get_secret("api-key")

# Get a JSON secret
config = credential_manager.get_json_secret("config")

# Get a service account key
sa_key = credential_manager.get_service_account_key("vertex-ai-agent")
```

### Using the FastAPI Dependencies

```python
from fastapi import Depends, FastAPI
from core.orchestrator.src.api.dependencies.credentials import (
    get_vertex_ai_credentials,
    get_gemini_credentials,
    get_redis_credentials,
)

app = FastAPI()

@app.post("/vertex/predict")
async def predict(
    request: PredictRequest,
    credentials: dict = Depends(get_vertex_ai_credentials)
):
    # Use credentials to access Vertex AI
    return {"prediction": "result"}
```

### Using the Example Script

Run the example script to see the credential management system in action:

```bash
# Make the script executable
chmod +x examples/credential_management_example.py

# Run the example script
./examples/credential_management_example.py
```

## Maintenance

### Credential Rotation

Credentials are automatically rotated using Cloud Scheduler and Cloud Functions. The rotation schedule is defined in the Terraform configuration.

To manually rotate a credential:

```bash
# Rotate a service account key
./secure_credential_manager.sh rotate-key service-account@project-id.iam.gserviceaccount.com
```

### Syncing GitHub and GCP Secrets

To sync secrets between GitHub and GCP:

```bash
# Run the sync script
./sync_github_gcp_secrets.sh
```

### Updating the Infrastructure

To update the infrastructure:

```bash
# Run the implementation plan script
./implementation_plan.sh
```

Select the appropriate option to update the infrastructure.

## Security Best Practices

1. **No Hardcoded Credentials**: Never hardcode credentials in code or configuration files.

2. **Least Privilege**: Use service accounts with only the permissions they need.

3. **Short-Lived Credentials**: Use Workload Identity Federation when possible, and rotate service account keys regularly.

4. **Secure Storage**: Store all credentials in Secret Manager.

5. **Audit Logging**: Enable audit logging for all credential access.

6. **Environment Isolation**: Use separate credentials for different environments.

7. **Credential Rotation**: Rotate credentials regularly.

8. **Secure Transmission**: Always use HTTPS/TLS for credential transmission.

9. **Access Control**: Restrict access to credentials based on the principle of least privilege.

10. **Monitoring and Alerting**: Set up monitoring and alerting for credential usage.

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
   Error: Secret not found: projects/cherry-ai-project/secrets/secret-name
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
4. Refer to the documentation in the `docs` directory