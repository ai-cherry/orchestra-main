# GCP Migration Toolkit

## Overview

A comprehensive toolkit for migrating from GitHub Codespaces to Google Cloud Workstations, providing seamless transition with minimal disruption to development workflows.

This toolkit simplifies the migration process by automating resource inventories, handling repository transfers, managing secrets, and configuring GCP Workstation environments that replicate your existing GitHub Codespaces setup.

## Key Features

- **Comprehensive Pre-Migration Assessment**: Automatically inventory repositories, extensions, dependencies, and configurations
- **Secure Resource Migration**: Safely transfer repositories, secrets, and configurations with validation at each step
- **Infrastructure as Code**: Generate Terraform configurations for GCP Workstations environments
- **AI Coding Tool Integration**: Seamlessly configure Gemini Code Assist and other AI tools in your new environment
- **Resilient Operations**: Built-in circuit breakers, retry mechanisms, and validation ensure robust migration
- **Multiple Interfaces**: Use the toolkit via CLI, REST API, or programmatic Python interface

## Installation

### Using Poetry (Recommended)

```bash
# Clone this repository
git clone https://github.com/your-org/gcp-migration.git
cd gcp-migration

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
# Install from PyPI
pip install gcp-migration

# Or install directly from GitHub
pip install git+https://github.com/your-org/gcp-migration.git
```

## Prerequisites

- Python 3.11+
- Google Cloud SDK installed and configured
- Access to your GitHub organization/repositories
- Appropriate GCP permissions to create resources

## Quick Start

### Basic Migration

```bash
# Initialize a migration configuration template
gcp-migrate init --github-repo your-org/your-repo --gcp-project your-gcp-project-id

# Edit the generated configuration file with your specific details
# Then run the migration
gcp-migrate migrate --config migration_config.yaml
```

### Validate Without Execution

```bash
gcp-migrate validate --config migration_config.yaml
```

### Generate Cloud Workstation Configuration

```bash
gcp-migrate generate-workstation-config --project your-gcp-project-id --name dev-workstation-cluster
```

## Migration Configuration

The migration configuration file controls all aspects of the migration process. Here's an example:

```yaml
migration_type: github-to-gcp
source:
  type: github
  repository: your-org/your-repo
  branch: main
  use_oauth: false
  auth_method: personal_access_token
destination:
  type: gcp
  project_id: your-gcp-project-id
  location: us-central1
  use_application_default: true
options:
  parallel_resources: true
  validate_only: false
  dry_run: false
  skip_validation: false
resources:
  - id: secret1
    name: github-token
    type: SECRET
    source_path: GITHUB_TOKEN
  - id: config1
    name: app-config
    type: CONFIGURATION
    source_path: .devcontainer/devcontainer.json
    destination_path: gs://bucket-name/configs/devcontainer.json
```

## API Usage

The toolkit also provides a FastAPI-based REST API for integration with other tools:

```bash
# Start the API server
python -m gcp_migration.application.api
```

Then make requests like:

```bash
curl -X POST http://localhost:8000/migrations/github-to-gcp \
  -H "Content-Type: application/json" \
  -d '{
    "github_repository": "your-org/your-repo",
    "github_branch": "main",
    "gcp_project_id": "your-gcp-project-id",
    "resources": [
      {
        "id": "secret1",
        "name": "github-token",
        "type": "SECRET",
        "source_path": "GITHUB_TOKEN"
      }
    ]
  }'
```

## Programmatic Usage

You can also use the toolkit programmatically in your Python code:

```python
import asyncio
from gcp_migration.application.migration_service import MigrationService
from gcp_migration.domain.models import GithubConfig, GCPConfig, MigrationResource, ResourceType

async def run_migration():
    # Create service
    service = MigrationService(default_project_id="your-gcp-project-id")
    await service.initialize()
    
    # Configure source and destination
    github_config = GithubConfig(repository="your-org/your-repo", branch="main")
    gcp_config = GCPConfig(project_id="your-gcp-project-id", location="us-central1")
    
    # Define resources to migrate
    resources = [
        MigrationResource(
            id="secret1",
            name="github-token",
            type=ResourceType.SECRET,
            source_path="GITHUB_TOKEN"
        )
    ]
    
    # Create and execute migration plan
    plan = await service.create_github_to_gcp_plan(
        github_config=github_config,
        gcp_config=gcp_config,
        resources=resources
    )
    
    result = await service.execute_plan(plan)
    print(f"Migration succeeded: {result.success}")

if __name__ == "__main__":
    asyncio.run(run_migration())
```

## Architecture

The toolkit is designed using clean architecture principles with three main layers:

1. **Domain Layer**: Core business logic and domain models
   - Models represent migration resources, contexts, and results
   - Business rules and validation logic

2. **Application Layer**: Orchestration and workflow
   - Migration service coordinates the migration process
   - Workflows define the step-by-step migration execution
   - API and CLI interfaces expose functionality

3. **Infrastructure Layer**: External integrations
   - GCP service clients for storage, secrets, etc.
   - GitHub API integration
   - Connection and resilience mechanisms

## Development

### Project Structure

```
gcp_migration/
├── domain/                  # Domain models and interfaces
│   ├── models.py            # Core domain entities
│   └── exceptions_fixed.py  # Exception hierarchy
├── infrastructure/          # Infrastructure implementations
│   ├── connection.py        # Connection pooling
│   ├── resilience.py        # Circuit breakers and retry logic
│   └── gcp_service.py       # GCP service clients
├── application/             # Application services
│   ├── migration_service.py # Main migration service
│   ├── workflow.py          # Workflow orchestration
│   ├── api.py               # FastAPI interface
│   └── cli.py               # CLI interface
└── __main__.py              # Entry point
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=gcp_migration
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `poetry run pytest`
5. Submit a pull request

## License

MIT License