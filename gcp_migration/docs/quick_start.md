# GCP Migration Toolkit Quick Start Guide

This guide will help you quickly get started with the GCP Migration toolkit for the most common migration tasks.

## Prerequisites

- Python 3.8 or later
- GCP project with owner permissions
- GitHub repository access (if migrating from GitHub)
- [GCP Migration Toolkit installed](installation.md)

## 1. Authenticate with GCP

```bash
# Login with your Google account
gcloud auth login

# Set application default credentials
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## 2. Basic Project Setup

### Using CLI

```bash
# Setup project with required APIs and basic configuration
python -m gcp_migration.cli.app setup-project --project-id YOUR_PROJECT_ID
```

### Using Python API

```python
from gcp_migration.infrastructure.extended_gcp_service import ExtendedGCPService

# Initialize service
gcp_service = ExtendedGCPService(project_id="YOUR_PROJECT_ID")

# Enable required APIs
gcp_service.enable_gcp_apis([
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com"
])

# Verify setup
project_info = gcp_service.get_project_info()
print(f"Project setup complete for: {project_info['name']}")
```

## 3. Migrate GitHub Secrets

### Using CLI

```bash
# Migrate secrets from a GitHub repository to GCP Secret Manager
python -m gcp_migration.cli.app migrate-secrets \
  --github-org YOUR_GITHUB_ORG \
  --github-repo YOUR_GITHUB_REPO \
  --project-id YOUR_PROJECT_ID \
  --github-token YOUR_GITHUB_TOKEN
```

### Using Python API

```python
import asyncio
from gcp_migration.infrastructure.secret_manager_service import SecretManagerService

async def migrate_secrets():
    # Initialize service
    secret_service = SecretManagerService(github_token="YOUR_GITHUB_TOKEN")
    
    # Migrate GitHub secrets
    result = await secret_service.migrate_github_secrets(
        github_org="YOUR_GITHUB_ORG",
        github_repo="YOUR_GITHUB_REPO",
        project_id="YOUR_PROJECT_ID"
    )
    
    print(f"Migrated {result['migrated']} secrets")
    print(f"Skipped {result['skipped']} secrets")
    print(f"Failed {result['failed']} secrets")

# Run the async function
asyncio.run(migrate_secrets())
```

## 4. Setup Gemini Code Assist

### Using CLI

```bash
# Setup Gemini Code Assist
python -m gcp_migration.cli.app setup-gemini \
  --api-key YOUR_GEMINI_API_KEY \
  --workspace-path /path/to/your/workspace
```

### Using Python API

```python
from gcp_migration.infrastructure.gemini_config_service import GeminiConfigService

# Initialize service
gemini_service = GeminiConfigService(workspace_path="/path/to/your/workspace")

# Setup Gemini configuration
config_path = gemini_service.setup_gemini_config(api_key="YOUR_GEMINI_API_KEY")
print(f"Gemini configuration created at: {config_path}")

# Setup MCP memory system
memory_path = gemini_service.setup_mcp_memory()
print(f"MCP memory configured at: {memory_path}")

# Install required extensions
installed_extensions = gemini_service.install_extensions()
print(f"Installed {len(installed_extensions)} extensions")

# Verify installation
status = gemini_service.verify_installation()
if all(status.values()):
    print("Gemini Code Assist setup complete and verified!")
else:
    print("Some Gemini components could not be verified:")
    for component, verified in status.items():
        if not verified:
            print(f"- {component}: Not verified")
```

## 5. Verify Migration

### Using CLI

```bash
# Verify migration status
python -m gcp_migration.cli.app verify-migration --project-id YOUR_PROJECT_ID
```

### Using Python API

```python
from gcp_migration.infrastructure.extended_gcp_service import ExtendedGCPService
from gcp_migration.infrastructure.gemini_config_service import GeminiConfigService

# Initialize services
gcp_service = ExtendedGCPService(project_id="YOUR_PROJECT_ID")
gemini_service = GeminiConfigService()

# Verify GCP setup
api_status = gcp_service.check_gcp_apis_enabled()
print("API Status:")
for api, enabled in api_status.items():
    print(f"- {api}: {'Enabled' if enabled else 'Disabled'}")

# Verify secrets
secrets = gcp_service.list_secrets()
print(f"Found {len(secrets)} secrets in Secret Manager")

# Verify Gemini setup
gemini_status = gemini_service.verify_installation()
print("Gemini Status:")
for component, status in gemini_status.items():
    print(f"- {component}: {'Verified' if status else 'Not verified'}")
```

## 6. Error Handling Example

```python
from gcp_migration.core.errors import (
    handle_exception, 
    MigrationError, 
    ResourceNotFoundError, 
    ErrorSeverity
)
import logging

logger = logging.getLogger(__name__)

@handle_exception(
    logger=logger,
    default_error_type=MigrationError,
    error_message="Failed to complete migration operation",
    re_raise=True,
    log_traceback=True,
    severity=ErrorSeverity.ERROR
)
def perform_migration_operation(project_id):
    # Your migration code here
    if not project_id:
        raise ValueError("Project ID cannot be empty")
    
    # If a resource is not found
    if project_id == "invalid-project":
        raise ResourceNotFoundError("Project not found")
    
    return True

# Usage
try:
    result = perform_migration_operation("your-project-id")
    print(f"Migration operation completed: {result}")
except MigrationError as e:
    print(f"Migration failed: {e}")
    # Handle the error appropriately
```

## Next Steps

After completing these basic steps, you might want to:

1. Explore the [complete API reference](api_reference.md)
2. Learn about [error handling](error_handling.md) for more robust applications
3. Check out [security best practices](security_best_practices.md) for production deployments

For more detailed guides, see the [Documentation Index](index.md).
