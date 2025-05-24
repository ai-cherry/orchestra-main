# MCP Server Setup and Troubleshooting Guide

This document provides instructions for setting up and running the MCP (Model Context Protocol) server, along with troubleshooting tips for common issues.

## Overview

The MCP server provides memory and tool capabilities for AI agents in the AI Orchestra project. It can be run in several ways:

- Direct execution (recommended for development)
- Docker container (recommended for production)
- Systemd service (for long-running server instances)

## Prerequisites

- Python 3.8 or higher
- Poetry (will be installed automatically if missing)
- Docker (optional, for containerized deployment)
- systemd (optional, for service-based deployment)

## Running the MCP Server

### Option 1: Using the Startup Script

The simplest way to start the MCP server is using the provided script:

```bash
./mcp_server/scripts/start_mcp_server.sh
```

This script will:

1. Detect your environment (Docker, GitHub Codespace, or standard)
2. Install required dependencies if needed
3. Start the MCP server in the appropriate mode
4. Provide status information

### Option 2: Using Docker

For containerized deployment, use Docker Compose:

```bash
cd mcp_server/scripts
docker-compose up -d
```

This will build and start the MCP server in a Docker container, with proper volume mounting for persistent data.

### Option 3: Using Systemd (Linux only)

For systems with systemd, you can install and run as a service:

```bash
sudo ./mcp_server/scripts/start_mcp_server.sh
```

The script will detect systemd and install/start the service automatically.

## Configuration

The MCP server uses a configuration file located at:

```
/workspaces/orchestra-main/mcp_server/config.json
```

If this file doesn't exist, it will be created automatically from the example configuration.

## Troubleshooting

### Common Issues

#### 1. "Poetry not found"

**Solution**: The startup script has been updated to handle this automatically by:

- Installing Poetry using the official installer
- Adding Poetry to the PATH for the current session
- Providing a clear error message if Poetry cannot be installed

#### 2. "ModuleNotFoundError: No module named 'flask'"

**Solution**: The startup script should install required dependencies. If this error persists:

- Manually install dependencies: `cd mcp_server && poetry install`
- Check if your Python environment is correctly set up

#### 3. "Address already in use"

**Solution**: The MCP server is already running or another service is using port 8080.

- Check for running instances: `pgrep -f "python.*mcp_server.main"`
- Kill existing instances: `pkill -f "python.*mcp_server.main"`
- Change the port in the configuration file

#### 4. Docker-related issues

**Solution**:

- Ensure Docker is installed and running
- Check Docker logs: `docker logs mcp-server_mcp-server_1`
- Rebuild the container: `docker-compose build --no-cache`

## Logs and Monitoring

- Log file location: `/tmp/mcp-server.log`
- To check the status: `http://localhost:8080/api/status`
- To stop the server: `pkill -f 'python.*mcp_server.main'`

## Integration with AI Orchestra

The MCP server is designed to work with the AI Orchestra project. For integration details, refer to the API documentation and examples in the project repository.

## Advanced Configuration

For advanced configuration options, including memory persistence, tool adapters, and authentication, refer to the full documentation in the `mcp_server/docs` directory.

## Dependency Management

The MCP server uses Poetry for dependency management, which provides several benefits:

- Deterministic builds with locked dependencies
- Separate development and production dependencies
- Virtual environment management
- Easy package publishing and versioning

### Adding New Dependencies

To add a new dependency:

```bash
cd mcp_server
poetry add package-name
```

For development dependencies:

```bash
cd mcp_server
poetry add --group dev package-name
```

### Updating Dependencies

To update dependencies:

```bash
cd mcp_server
poetry update
```

### Managing Virtual Environments

Poetry automatically creates and manages virtual environments. To activate the virtual environment:

```bash
cd mcp_server
poetry shell
```

To run a command within the virtual environment without activating it:

```bash
cd mcp_server
poetry run command
```
