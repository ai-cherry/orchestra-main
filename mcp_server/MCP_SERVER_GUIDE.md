# MCP Server Management Guide

## Overview

The Model Context Protocol (MCP) servers provide specialized tools and capabilities to AI agents like Claude Code within the Cursor IDE. This guide covers setup, management, and troubleshooting of MCP servers, primarily focusing on a Vultr-hosted environment with PostgreSQL and Weaviate Cloud.

## Quick Start

### Setup AI Agent with MCP

```bash
# (Assuming a generic setup script for your AI agent)
./scripts/setup_ai_agent_with_mcp.sh 
```

### Launch Cursor with MCP Servers (Example)

```bash
./launch_cursor_with_mcp.sh # Example, depends on your specific Cursor launch script
```

### Check Server Status

```bash
./check_mcp_servers.sh
```

## Server Management

### Using the Management Script

The `manage_mcp_servers.sh` script provides comprehensive server control:

```bash
# List available servers
./manage_mcp_servers.sh list

# Start all servers
./manage_mcp_servers.sh start

# Start specific server (e.g., a memory cache server)
./manage_mcp_servers.sh start memory_cache_server 

# Check status
./manage_mcp_servers.sh status

# Stop servers (e.g., a specific tool server)
./manage_mcp_servers.sh stop code_analysis_tool_server

# Restart servers
./manage_mcp_servers.sh restart
```

### Available Servers (Example Vultr-centric Setup)

1.  **`vultr-app-deployer`** - Deploy and manage applications on Vultr instances.
    *   Required: `VULTR_API_KEY`
    *   Capabilities: deploy, update, status, list, logs, scale (via instance changes or auto-scaling groups if configured)

2.  **`secret-manager-tool`** - Manage secrets (e.g., using HashiCorp Vault on Vultr, or environment variables for simpler setups).
    *   Required: Depends on chosen secret management solution (e.g., `VAULT_ADDR`, `VAULT_TOKEN`)
    *   Capabilities: get, create, update, list, versions

3.  **`memory-cache-server`** - Short-term memory cache (e.g., Redis or DragonflyDB hosted on Vultr).
    *   Optional: `CACHE_HOST`, `CACHE_PORT`, `CACHE_PASSWORD`
    *   Capabilities: get, set, delete, list, ttl, pipeline

4.  **`document-db-manager`** - Mid-term episodic memory (e.g., PostgreSQL with JSONB, or a dedicated DocumentDB on Vultr).
    *   Required: `POSTGRES_URL` (if using PostgreSQL for this)
    *   Capabilities: create, read, update, query, batch, transaction

## Logging and Debugging

### Log Locations

- Setup logs: `~/.orchestra-ai/logs/setup_*.log` (Example path)
- Server logs: `~/.orchestra-ai/logs/mcp_<server_name>_<date>.log`
- Launch logs: `~/.orchestra-ai/logs/cursor_launch_*.log`

### Viewing Logs

```bash
# View latest setup log
tail -f ~/.orchestra-ai/logs/setup_*.log

# View specific server log (e.g., memory_cache_server)
tail -f ~/.orchestra-ai/logs/mcp_memory_cache_server_*.log

# Check for errors
grep -i ERROR ~/.orchestra-ai/logs/*.log
```

### Common Issues and Solutions

1.  **Server won't start**
    *   Check if required environment variables are set (e.g., `VULTR_API_KEY`, `POSTGRES_URL`).
    *   Verify Python dependencies are installed (`poetry install`).
    *   Check log files for specific errors.

2.  **Server crashes immediately**
    *   Run syntax check: `python -m py_compile <server_file.py>`
    *   Check for missing imports or dependencies.
    *   Verify Vultr API key and other credentials if services interact with Vultr.

3.  **Connection refused**
    *   Ensure backend services are running (PostgreSQL, Weaviate Cloud, Cache DB on Vultr).
    *   Check firewall/network settings on Vultr and within instances.
    *   Verify connection parameters in environment variables.

## Server Registry

The server registry (e.g., `mcp_server/server_registry.json`) defines available servers and their requirements:

```json
{
  "version": "1.0.0",
  "servers": {
    "example_tool_server": {
      "path": "servers/example_tool_server.py",
      "command": "python",
      "description": "An example tool server",
      "required_env": ["TOOL_API_KEY"],
      "optional_env": ["TOOL_CONFIG_PATH"]
    }
  }
}
```

## Creating New Servers

Use the template at `mcp_server/servers/example_server.py.template` as a starting point:

1.  Copy the template:
    ```bash
    cp mcp_server/servers/example_server.py.template mcp_server/servers/my_new_tool_server.py
    ```
2.  Implement your server logic.
3.  Add to server registry.
4.  Test the server:
    ```bash
    python mcp_server/servers/my_new_tool_server.py
    ```
5.  Add to management scripts if needed.

## Environment Setup

### Required Environment Variables

Set these in a `.env` file or your shell profile (e.g., `~/.bashrc.orchestra`):

```bash
export VULTR_API_KEY="your_vultr_api_key"
export POSTGRES_URL="postgresql://user:pass@your_vultr_postgres_host:port/dbname"
export WEAVIATE_URL="your_weaviate_cloud_url"
export WEAVIATE_API_KEY="your_weaviate_api_key"

# Optional for Cache DB (e.g., Redis/DragonflyDB on Vultr)
export CACHE_HOST="your_vultr_cache_db_host"
export CACHE_PORT="6379"
export CACHE_PASSWORD="your_cache_password"
```

### Loading Environment
Ensure your scripts source the environment file or that variables are present in the execution environment.

## Integration with AI Agents (e.g., Claude Code)

### Using MCP Tools in AI Agents

Once MCP servers are running, you can use their tools in your AI agents:

```
# Deploy application to Vultr
"Deploy my FastAPI app to a Vultr instance using the vultr-app-deployer tool"

# Secret Management (example with a generic tool)
"Get the database password using the secret-manager-tool"

# Caching
"Cache this user profile in memory_cache_server with key user:123"

# Document DB Operations (example with PostgreSQL JSONB)
"Store this conversation in document-db-manager under conversations collection"
```

### MCP Configuration
AI agent configuration (e.g., for Claude Code via Cursor) should point to the MCP server endpoints.
This is usually managed via the orchestrator or agent-specific settings.

## Monitoring and Health Checks

### Server Health
Launch scripts for MCP servers often include basic monitoring:
- Checks if servers are still running.
- Attempts to restart crashed servers.
- Logs events for debugging.

### Manual Health Check

```bash
# Check if server process is running (example)
ps aux | grep mcp_server # General check
ps aux | grep memory_cache_server.py # Specific server

# Check specific server PID (if your scripts manage PIDs)
# cat ~/.orchestra-ai/pids/mcp_memory_cache_server.pid
# kill -0 $(cat ~/.orchestra-ai/pids/mcp_memory_cache_server.pid)
```

## Best Practices

1.  **Always check logs** when servers fail to start.
2.  **Set up environment variables** correctly before running servers.
3.  **Use the management script** for consistent server control.
4.  **Monitor resource usage** on Vultr instances hosting MCP servers.
5.  **Restart servers** if they become unresponsive, using the management script.
6.  **Keep server dependencies updated** using Poetry.

## Troubleshooting Commands

```bash
# Check Python version
python --version

# Verify imports for a specific server script
# python -c "import mcp_server.servers.your_server_module"

# Test Vultr API key (if vultr-cli is installed)
# vultr-cli account

# Check if ports are in use (e.g., for a service on port 8001)
ss -tulnp | grep :8001

# Clear PID files if needed (example path)
# rm ~/.orchestra-ai/pids/*.pid

# Full system check (using your scripts)
./check_mcp_servers.sh && ./manage_mcp_servers.sh status
```

## Support

For issues:

1.  Check the logs first (`~/.orchestra-ai/logs/`).
2.  Verify environment setup (`.env` file or shell profile).
3.  Consult server-specific documentation if applicable.
4.  Check the example server template for patterns.
