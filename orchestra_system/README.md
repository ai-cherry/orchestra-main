# AI Orchestra System

## Overview

The AI Orchestra System is a comprehensive framework designed to streamline AI assistants' real-time awareness of development resources in a hybrid GCP-GitHub-Codespaces environment. It addresses the key challenges of maintaining context, handling configuration across environments, detecting and resolving conflicts, and providing a unified interface for AI tools.

## Architecture

The system consists of four main components:

1. **Resource Registry** - Discovers and tracks available development resources
2. **Configuration Manager** - Handles configuration across different environments
3. **Conflict Resolver** - Detects and resolves conflicts between files, resources, and configurations
4. **System API** - Provides a unified interface to interact with all components

These components work together to provide AI assistants with real-time awareness of available resources, appropriate configurations, and potential conflicts.

![Architecture Diagram](https://mermaid.ink/img/pako:eNqFksFu2zAMhl-F4FkyxynaAL2kQYxlQ4HCa7zLbhYto7Y2W4JMKlDRvPtox0mKNcWObCT-_MS_FJv0YRPJUZ58Z5_LbLzqIiVsOtNqPp6SkdSH-nE7JpXOsEsS9fRcmpzUB7Kp_0vCcnQmYYO1zcJvLrQtdcxdxzQ0xZR3-XAHLHJjMDkMOl0VLKXnDl3HfD8uDIePWXbcbrdZ9dn5LE--NyomDG2OE9NxF6h_cg5NtJrttLPJzQPZQU9Bq3lIGLVSRzVJ_bQ5-7Sq5B1vygFyQfYQeyzLFRxhqqoJJmO1IlzLkVVVVXUecJ1NlhDCDpZoCrpAOPi_WjHg-9sTDYTBoK_U0Wo97JnhAT4BcPT8-F1M_MBncUF0O3cKWOcVdLmLo_TuDN_6-Ggww2DCOhrsOnbBSgYzBpRZNsZ5ejcZqeG5GaBIPF2zHExeGv5jlIUcvKmLtZT_9E_pN3ksbS7pZeudSbVNLvC9OaWXpj2MeLhc7WJe3O-P-b9o1V2jSE-BxKRx9J4VUufp5bc8_wXBfMRB)

## Installation

### Prerequisites

- Python 3.11+
- Access to GCP resources (for full functionality)
- GitHub repository access
- Virtual environment (recommended)

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/ai-orchestra.git
   cd ai-orchestra
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT=cherry-ai-project
   export DEPLOYMENT_ENV=development  # or production, staging, etc.
   ```

## Components

### Resource Registry

The Resource Registry discovers, tracks, and provides information about available development resources across different environments.

**Key features:**

- Automatic resource discovery
- Environment-specific resource tracking
- Resource status verification
- Resource type categorization

**Resource types:** CLI tools, API clients, GCP services, GitHub actions, credentials, configuration files, AI models, and more.

#### Usage Example

```python
from orchestra_system.resource_registry import get_registry, discover_resources

# Get resource registry
registry = get_registry()

# Discover resources
resources = await discover_resources()
print(f"Discovered {len(resources)} resources")

# Get resources by type
gcp_resources = registry.list_resources(resource_type=ResourceType.GCP_SERVICE)
```

### Configuration Manager

The Configuration Manager handles configuration values across different environments, detects conflicts, and provides a unified interface for accessing configuration.

**Key features:**

- Environment-aware configuration
- Automatic conflict detection and resolution
- Configuration validation
- Import/export capabilities

**Configuration sources:** Environment variables, .env files, JSON/YAML files, Terraform variables, and more.

#### Usage Example

```python
from orchestra_system.config_manager import get_manager, get, set

# Get configuration manager
config_manager = get_manager()

# Discover configuration
config_count = config_manager.discover_configuration()

# Access configuration
api_key = get("api.key", default="default-key")

# Set configuration
set("database.url", "postgresql://user:pass@localhost:5432/db")

# Validate configuration
is_valid, errors = config_manager.validate()
```

### Conflict Resolver

The Conflict Resolver detects and resolves conflicts between files, resources, and configurations.

**Key features:**

- Multiple conflict detection strategies
- Automated and manual resolution options
- Resolution history tracking
- Integration with MCP memory

**Conflict types:** Duplicate files, file conflicts, resource conflicts, configuration conflicts, reference inconsistencies, and more.

#### Usage Example

```python
from orchestra_system.conflict_resolver import get_resolver, detect_conflicts

# Get conflict resolver
resolver = get_resolver()

# Detect conflicts
conflicts = detect_conflicts()
print(f"Detected {len(conflicts)} conflicts")

# Resolve a conflict
resolution = resolver.resolve_conflict(
    conflict_id="duplicate_file_abc123",
    strategy=ResolutionStrategy.DELETE_DUPLICATE
)

# Apply resolution
success = resolver.apply_resolution(resolution.conflict_id)
```

### System API

The System API provides a unified interface to interact with all components of the AI Orchestra System.

**Key features:**

- Unified interface for all system components
- Asynchronous API design
- Context awareness for AI assistants
- System state tracking

#### Usage Example

```python
from orchestra_system.api import get_api, initialize_system

# Get system API
api = get_api()

# Initialize the system
state = await api.initialize_system()

# Get resources
resources = await api.get_resources(resource_type="gcp_service")

# Get configuration
api_key = api.get_configuration("api.key")

# Get conflicts
conflicts = api.get_conflicts(status="pending")

# Get system context for AI assistants
context = await api.get_context()
```

## CLI Usage

Each component can be used from the command line for quick operations:

### Resource Registry

```bash
# Discover resources
python -m orchestra_system.resource_registry --discover

# List resources
python -m orchestra_system.resource_registry --list
```

### Configuration Manager

```bash
# Discover configuration
python -m orchestra_system.config_manager --discover

# Export configuration
python -m orchestra_system.config_manager --export config.json

# Import configuration
python -m orchestra_system.config_manager --import config.json
```

### Conflict Resolver

```bash
# Detect conflicts
python -m orchestra_system.conflict_resolver --detect

# List conflicts
python -m orchestra_system.conflict_resolver --list

# Resolve a conflict
python -m orchestra_system.conflict_resolver --resolve CONFLICT_ID --strategy priority
```

### System API

```bash
# Initialize the system
python -m orchestra_system.api --init

# Get context
python -m orchestra_system.api --context

# Clean up artifacts
python -m orchestra_system.api --cleanup --dry-run
```

## Integration with AI Assistants

The AI Orchestra System is designed to integrate seamlessly with AI assistants through the MCP (Model Context Protocol) memory system.

### Example Integration

```python
# Get AI context
from orchestra_system.api import get_api

async def get_ai_context():
    api = get_api()
    context = await api.get_context()
    return context

# Use context in AI assistant
context = await get_ai_context()
print(f"Available resources: {context['resources']['total']}")
print(f"Configuration valid: {context['configuration']['is_valid']}")
print(f"Pending conflicts: {context['conflicts']['pending']}")
```

## Best Practices

1. **Regular Resource Discovery**

   - Run resource discovery periodically to maintain an up-to-date registry.

2. **Environment-Specific Configuration**

   - Use environment-specific configuration to handle differences between environments.

3. **Conflict Detection and Resolution**

   - Run conflict detection before making significant changes to the codebase.
   - Resolve conflicts as soon as they are detected to prevent issues.

4. **Artifact Cleanup**

   - Regularly clean up development artifacts to prevent clutter.

5. **System Context Awareness**
   - Use the system context in AI assistants to provide relevant information.

## Architecture Decisions

### MCP Memory Integration

The system uses MCP (Model Context Protocol) memory to provide context persistence across AI assistant sessions. This allows assistants to maintain awareness of available resources, configuration, and conflicts even when they're restarted.

### Environment-Aware Components

All components are environment-aware, allowing them to provide different behavior based on the current environment (local, Codespaces, GCP Cloud Run, etc.). This is crucial for handling environment-specific resources and configuration.

### Conflict Resolution Strategies

Multiple conflict resolution strategies are provided to handle different types of conflicts. Strategies include:

- Priority-based resolution (highest priority wins)
- Environment-based resolution (current environment wins)
- Timestamp-based resolution (newest wins)
- Merge-based resolution (combine conflicting items)
- Manual resolution (user decides)

### Resource Type Categorization

Resources are categorized by type to provide better organization and filtering capabilities. This allows AI assistants to quickly find relevant resources for specific tasks.

## Frequently Asked Questions

### How does the system handle environment differences?

The system detects the current environment and provides environment-specific resources and configuration. This allows it to adapt to different environments without manual intervention.

### How are conflicts resolved automatically?

Conflicts are resolved using various strategies based on the conflict type. For example, duplicate files can be resolved by keeping only one copy, while configuration conflicts can be resolved by priority or environment.

### Can I extend the system with custom components?

Yes, the system is designed to be extensible. You can add custom resource types, configuration sources, conflict detection strategies, and more.

### How does the system integrate with CI/CD pipelines?

The system can be used in CI/CD pipelines to detect conflicts, validate configuration, and clean up artifacts. This helps ensure a smooth deployment process.

## Troubleshooting

### Resource Registry Not Finding Resources

- Ensure the resource discovery process has been run.
- Check if the current environment matches the resource's environment.
- Verify that the resource exists and is accessible.

### Configuration Conflicts

- Run the configuration validation to identify conflicts.
- Use the conflict resolver to resolve configuration conflicts.
- Check for environment-specific configuration that might conflict.

### Conflict Resolution Failures

- Check if the conflict exists in the registry.
- Ensure the resolution strategy is appropriate for the conflict type.
- Try a different resolution strategy if the current one fails.

### MCP Memory Integration Issues

- Verify that the MCP client is available and properly configured.
- Check for errors in the MCP memory system logs.
- Ensure the correct keys are being used for storing and retrieving data.

## Contributing

We welcome contributions to the AI Orchestra System! Here's how you can contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and add tests if applicable.
4. Run the tests to ensure they pass.
5. Submit a pull request with a description of your changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
