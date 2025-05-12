# MCP Server Startup Fix

This document outlines the changes made to fix the MCP (Model Context Protocol) server startup issues.

## Issue Summary

The MCP server was encountering startup failures due to:

1. **Package Structure Issues**: Inconsistent package structure with duplicate nested directories
2. **Import Path Problems**: Relative imports that failed when running as a script or installed package
3. **Poetry Configuration**: Mismatched entry point definitions in pyproject.toml

## Changes Made

### 1. Fixed Package Declaration

Updated `pyproject.toml` to correctly specify the package structure:

```toml
packages = [{include = "mcp_server"}]
```

### 2. Fixed Entry Point Configuration

Updated the Poetry entry point to correctly reference the main module:

```toml
[tool.poetry.scripts]
mcp-server = "mcp_server.main:main"
```

### 3. Standardized Import Paths

Changed all imports to use absolute import paths that properly reference the package structure:

```python
# Before
from config import load_config, MCPConfig

# After
from mcp_server.config import load_config, MCPConfig
```

### 4. Added Proper Type Hints

Added explicit type hints and null checks to prevent type errors:

```python
# Before
def __init__(self, config: dict = None):
    self.config = config or {}
    self.storage = None
    self.memory_manager = None

# After
def __init__(self, config: Optional[Dict[str, Any]] = None):
    self.config: Dict[str, Any] = config or {}
    self.storage: Optional[InMemoryStorage] = None
    self.memory_manager: Optional[StandardMemoryManager] = None
```

### 5. Updated Dockerfile

Updated the Dockerfile to use the correct entry point:

```dockerfile
CMD ["python", "-m", "mcp_server.run_mcp_server"]
```

### 6. Created Startup Helper Script

Added a simple startup script (`start_mcp_server.sh`) in the project root to simplify the development workflow.

## How to Run the MCP Server

### Option 1: Using the Startup Helper (Recommended for Development)

```bash
# From the project root
./start_mcp_server.sh
```

This script handles:
- Poetry installation (if needed)
- Dependencies installation
- Running the server with proper environment variables

### Option 2: Using Poetry Directly

```bash
# Navigate to the mcp_server directory
cd mcp_server

# Install dependencies
poetry install

# Run the server
poetry run python -m mcp_server.run_mcp_server --config ./config.json
```

### Option 3: Using Docker

```bash
# Build the Docker image
docker build -t mcp-server -f mcp_server/Dockerfile .

# Run the container
docker run -p 8080:8080 mcp-server
```

## Troubleshooting

If you encounter any issues:

1. Ensure Poetry is installed correctly
2. Verify that all dependencies are installed with `poetry install`
3. Check that the config.json file exists (copy from config.json.example if needed)
4. If import errors persist, try running `poetry lock --no-update` to rebuild the lock file

## Future Improvements

1. Add health check endpoint for proper monitoring in production
2. Implement graceful shutdown for better container orchestration
3. Add more comprehensive error handling for API keys and configuration
4. Create CI/CD pipeline test to verify server startup during deployment