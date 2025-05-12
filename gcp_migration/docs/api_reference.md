# GCP Migration Toolkit API Reference

This document provides a comprehensive reference for the API of the GCP Migration toolkit.

## Core Services

### ExtendedGCPService

The `ExtendedGCPService` class is the primary integration point with Google Cloud Platform.

#### Constructor

```python
def __init__(
    self, 
    project_id: str,
    credentials_path: Optional[str] = None,
    location: str = "us-central1"
):
    """
    Initialize the ExtendedGCPService.
    
    Args:
        project_id: The GCP project ID
        credentials_path: Optional path to service account key file
        location: The default GCP region/location for resource creation
    """
```

#### Core API Methods

```python
def check_gcp_apis_enabled(self, apis: List[str] = None) -> Dict[str, bool]:
    """
    Check if specific GCP APIs are enabled for the project.
    
    Args:
        apis: List of API service names to check, defaults to all required APIs
        
    Returns:
        Dictionary mapping API names to their enabled status
    """

def enable_gcp_apis(self, apis: List[str]) -> bool:
    """
    Enable specified GCP APIs for the project.
    
    Args:
        apis: List of API service names to enable
        
    Returns:
        True if all APIs were enabled successfully, False otherwise
    """

def get_project_info(self) -> Dict[str, Any]:
    """
    Get basic information about the configured GCP project.
    
    Returns:
        Dictionary containing project details (ID, name, number, etc.)
    """
```

#### Secret Manager Methods

```python
def store_secret(
    self, 
    secret_id: str, 
    secret_value: str,
    project_id: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None
) -> str:
    """
    Store a secret in Secret Manager.
    
    Args:
        secret_id: Secret identifier
        secret_value: Value to store
        project_id: Optional project ID (defaults to service project ID)
        labels: Optional labels for the secret
        
    Returns:
        Version name of the stored secret
    """

def retrieve_secret(
    self, 
    secret_id: str, 
    version: str = "latest",
    project_id: Optional[str] = None
) -> Optional[str]:
    """
    Retrieve a secret from Secret Manager.
    
    Args:
        secret_id: Secret identifier
        version: Secret version (defaults to "latest")
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        Secret value as string, or None if not found
    """

def delete_secret(
    self, 
    secret_id: str,
    project_id: Optional[str] = None
) -> bool:
    """
    Delete a secret from Secret Manager.
    
    Args:
        secret_id: Secret identifier
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        True if deletion was successful, False otherwise
    """
```

#### Storage Methods

```python
def upload_file(
    self, 
    bucket_name: str, 
    source_file_path: str,
    destination_blob_name: Optional[str] = None,
    project_id: Optional[str] = None
) -> str:
    """
    Upload a file to Cloud Storage.
    
    Args:
        bucket_name: Name of the destination bucket
        source_file_path: Path to the source file
        destination_blob_name: Optional destination path (defaults to filename)
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        Full GCS URI of the uploaded file
    """

def download_file(
    self, 
    bucket_name: str, 
    blob_name: str,
    destination_file_path: str,
    project_id: Optional[str] = None
) -> str:
    """
    Download a file from Cloud Storage.
    
    Args:
        bucket_name: Name of the source bucket
        blob_name: Name of the blob to download
        destination_file_path: Path where the file should be saved
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        Path to the downloaded file
    """

def list_bucket_contents(
    self, 
    bucket_name: str,
    prefix: Optional[str] = None,
    project_id: Optional[str] = None
) -> List[str]:
    """
    List contents of a Cloud Storage bucket.
    
    Args:
        bucket_name: Name of the bucket
        prefix: Optional prefix to filter results
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        List of blob names in the bucket
    """
```

#### Firestore Methods

```python
def store_document(
    self, 
    collection: str, 
    document_id: str, 
    data: Dict[str, Any],
    project_id: Optional[str] = None
) -> str:
    """
    Store a document in Firestore.
    
    Args:
        collection: Collection name
        document_id: Document identifier
        data: Document data to store
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        Full document path
    """

def retrieve_document(
    self, 
    collection: str, 
    document_id: str,
    project_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a document from Firestore.
    
    Args:
        collection: Collection name
        document_id: Document identifier
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        Document data as dictionary, or None if not found
    """

def query_documents(
    self, 
    collection: str, 
    filters: List[Tuple[str, str, Any]],
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query documents in Firestore.
    
    Args:
        collection: Collection name
        filters: List of filter tuples (field, operator, value)
        project_id: Optional project ID (defaults to service project ID)
        
    Returns:
        List of matching documents
    """
```

#### Vertex AI Methods

```python
def list_models(
    self, 
    filter_str: Optional[str] = None,
    project_id: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List available models in Vertex AI.
    
    Args:
        filter_str: Optional filter string
        project_id: Optional project ID (defaults to service project ID)
        location: Optional location (defaults to service location)
        
    Returns:
        List of model details
    """

def deploy_model(
    self, 
    model_id: str,
    machine_type: str = "n1-standard-4",
    project_id: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deploy a model to Vertex AI.
    
    Args:
        model_id: Model identifier
        machine_type: VM type for deployment
        project_id: Optional project ID (defaults to service project ID)
        location: Optional location (defaults to service location)
        
    Returns:
        Deployment details
    """
```

### SecretManagerService

The `SecretManagerService` provides specialized functionality for managing secrets.

#### Constructor

```python
def __init__(
    self, 
    gcp_service: Optional[IGCPSecretManager] = None,
    github_token: Optional[str] = None
):
    """
    Initialize the SecretManagerService.
    
    Args:
        gcp_service: Optional GCP service implementation
        github_token: Optional GitHub token for accessing GitHub secrets
    """
```

#### Methods

```python
async def migrate_github_secrets(
    self, 
    github_org: str,
    github_repo: str,
    project_id: str,
    environment: str = "prod"
) -> Dict[str, Any]:
    """
    Migrate secrets from GitHub to GCP Secret Manager.
    
    Args:
        github_org: GitHub organization
        github_repo: GitHub repository
        project_id: GCP project ID
        environment: Environment name for secret labeling
        
    Returns:
        Dictionary with migration results
    """

async def batch_migrate_secrets(
    self, 
    secrets: Dict[str, str],
    project_id: str,
    prefix: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Migrate a batch of secrets to GCP Secret Manager.
    
    Args:
        secrets: Dictionary mapping secret names to values
        project_id: GCP project ID
        prefix: Optional prefix for secret names
        labels: Optional labels for the secrets
        
    Returns:
        List of migrated secret names
    """

def validate_secret_value(
    self, 
    secret_id: str,
    expected_value: str,
    project_id: str
) -> bool:
    """
    Validate a secret's value.
    
    Args:
        secret_id: Secret identifier
        expected_value: Expected secret value
        project_id: GCP project ID
        
    Returns:
        True if the secret value matches the expected value
    """
```

### GeminiConfigService

The `GeminiConfigService` manages the setup and configuration of Gemini Code Assist.

#### Constructor

```python
def __init__(
    self, 
    gcp_service: Optional[IGeminiConfigService] = None,
    workspace_path: Optional[str] = None
):
    """
    Initialize the GeminiConfigService.
    
    Args:
        gcp_service: Optional GCP service implementation
        workspace_path: Optional workspace path for configuration
    """
```

#### Methods

```python
def setup_gemini_config(
    self, 
    api_key: Optional[str] = None,
    config_path: Optional[str] = None
) -> str:
    """
    Setup Gemini Code Assist configuration.
    
    Args:
        api_key: Optional Gemini API key
        config_path: Optional path for configuration file
        
    Returns:
        Path to the configuration file
    """

def setup_mcp_memory(
    self, 
    memory_path: Optional[str] = None
) -> str:
    """
    Setup MCP memory system for Gemini.
    
    Args:
        memory_path: Optional path for memory configuration
        
    Returns:
        Path to the memory configuration
    """

def verify_installation(self) -> Dict[str, bool]:
    """
    Verify that Gemini is properly installed and configured.
    
    Returns:
        Dictionary with verification results
    """

def install_extensions(self) -> List[str]:
    """
    Install required VS Code extensions for Gemini.
    
    Returns:
        List of installed extension IDs
    """
```

## CLI Interface

### CLI Usage

```bash
# View available commands
python -m gcp_migration.cli.app --help

# Setup GCP project
python -m gcp_migration.cli.app setup-project --project-id your-project-id

# Migrate GitHub secrets
python -m gcp_migration.cli.app migrate-secrets --github-org your-org --github-repo your-repo --project-id your-project-id

# Setup Gemini Code Assist
python -m gcp_migration.cli.app setup-gemini --api-key your-api-key

# Verify migration
python -m gcp_migration.cli.app verify-migration --project-id your-project-id
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `setup-project` | Configure GCP project for migration |
| `migrate-secrets` | Migrate secrets from GitHub to GCP |
| `setup-storage` | Setup Cloud Storage buckets |
| `setup-firestore` | Setup Firestore database |
| `setup-gemini` | Setup Gemini Code Assist |
| `verify-migration` | Verify migration status |
| `cleanup` | Clean up temporary resources |

## Error Handling

For information on error handling in the toolkit, see [Error Handling Documentation](error_handling.md).
