# Google Cloud Platform Authentication

This document explains how authentication with Google Cloud Platform (GCP) services is implemented in the Orchestrator system.

## Overview

Orchestrator supports multiple methods for authenticating with GCP services like Firestore, Cloud Run, Vertex AI, Secret Manager, and others. The authentication system is designed to be flexible, secure, and compatible with different deployment environments.

## Authentication Methods

The system supports three primary authentication methods, listed in order of precedence:

1. **Service Account JSON Content** (recommended for Codespaces/Cloud Run)
   - Provide the entire service account key JSON as a string via the `GCP_SA_KEY_JSON` environment variable
   - Ideal for containerized environments and CI/CD pipelines

2. **Service Account Key File**
   - Provide the path to a service account key file via the `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Familiar approach for developers who use the standard Google Cloud SDK

3. **Application Default Credentials (ADC)**
   - No explicit configuration needed if running in GCP environment
   - For local development, run `gcloud auth application-default login`
   - Simplest approach when running within GCP services

## Security Recommendations

When choosing an authentication method, consider these security recommendations:

- In production environments, use the most restricted service account that has only the permissions needed for your specific application
- Avoid downloading service account keys when possible; prefer Workload Identity Federation for production
- Rotate service account keys regularly if they must be used
- Store sensitive credentials in a secure manner (e.g., Secret Manager, environment variables, etc.)
- For local development, use Application Default Credentials when possible

## Implementation Details

The authentication system is implemented across several components:

### 1. GCP Auth Module

The `packages/shared/src/gcp/auth.py` module provides centralized authentication utilities, including:

- `get_gcp_credentials()`: Get credentials from various sources
- `setup_gcp_credentials_file()`: Set up credentials from environment variables
- `initialize_gcp_auth()`: Initialize authentication for the application
- `get_project_id()`: Get the project ID from various sources

### 2. Settings

The `core/orchestrator/src/config/settings.py` file includes GCP-specific settings:

- `GCP_PROJECT_ID`: The GCP project ID
- `GCP_SA_KEY_JSON`: Service account key JSON content
- `GCP_LOCATION`: Default GCP region for services
- `GOOGLE_CLOUD_PROJECT`: Alias for GCP_PROJECT_ID (for compatibility)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to credentials file

Helper methods include:
- `get_gcp_project_id()`: Get the project ID with fallback
- `get_gcp_credentials_info()`: Get a dictionary with credentials information

### 3. Client Integration

GCP clients are integrated with the authentication system:

- `FirestoreClient`: Uses the auth module for Firestore operations
- `RedisClient`: Supports Secret Manager for retrieving passwords
- `VertexAgentManager`: Uses the auth module for Vertex AI, Pub/Sub, etc.

## Usage Examples

### Initializing a Firestore Client

```python
# Using service account JSON content
from packages.shared.src.storage.firestore_client import FirestoreClient

# The client will automatically use credentials from environment variables
firestore = FirestoreClient()

# Or explicitly provide credentials
firestore = FirestoreClient(
    project_id="my-project",
    service_account_json=json_content
)

# Use the client
await firestore.save_document("collection", "doc_id", {"key": "value"})
```

### Handling Secrets in Redis

```python
from packages.shared.src.storage.redis_client import RedisClient

# Redis client can fetch the password from Secret Manager
redis = RedisClient(
    host="redis-host",
    port=6379,
    secret_id="redis-password", # Will be fetched from Secret Manager
    project_id="my-project"
)

# Use the client
await redis.set_cache("key", "value")
```

### Using Vertex AI

```python
from packages.vertex_client.vertex_agent_manager import VertexAgentManager

# Initialize with authentication
manager = VertexAgentManager(
    service_account_json=json_content
)

# The manager handles authentication for Vertex AI, Pub/Sub, etc.
result = manager.apply_terraform("dev")
```

## Environment Setup

To use GCP services, configure your `.env` file with the appropriate values:

```
# Project identification 
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-west2  # Default region

# Authentication (choose ONE method)
# Method 1: Service account key JSON content
GCP_SA_KEY_JSON={"type":"service_account","project_id":"...","private_key_id":"..."}

# Method 2: Path to service account key file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key-file.json

# Method 3: Use Application Default Credentials (ADC)
# No configuration needed
```

## Creating a Least-Privilege Service Account

For production deployments, it's recommended to create a dedicated service account with only the necessary permissions:

1. Create a new service account in the GCP Console:
   - Name: `orchestrator-runtime`
   - Description: "Least-privilege service account for the Orchestrator application"

2. Assign only the required roles:
   - `roles/datastore.user` - For Firestore access
   - `roles/redis.editor` - For Redis access (if using GCP Memorystore)
   - `roles/secretmanager.secretAccessor` - For accessing secrets
   - `roles/aiplatform.user` - For using Vertex AI services (if needed)
   - `roles/pubsub.publisher` & `roles/pubsub.subscriber` - For Pub/Sub (if needed)

3. Create a key for this service account and securely store it:
   - Either as `GCP_SA_KEY_JSON` environment variable, or
   - In a secure secret manager service

## Future Improvements

The authentication system can be improved in several ways:

- Support for Workload Identity Federation
- Service account impersonation
- More granular roles for different services
- Integration with CI/CD pipelines for automated deployment
