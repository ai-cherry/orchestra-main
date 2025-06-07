# MCP Server Automation

This document outlines the automation and integration features of the MCP (Model Control Plane) server system.

## Overview

The MCP server provides several automation features to streamline development and deployment:

1. **Auto-start**: The server can be configured to start automatically when the development environment initializes
2. **Health monitoring**: Automated health checks ensure the server is running properly
3. **Memory synchronization**: Automatic synchronization between memory stores
4. **Integration with development tools**: Seamless integration with Cursor IDE

## Startup Automation

The MCP server includes a startup script that can detect the environment and initialize the server appropriately:

```bash
./mcp_server/scripts/start_mcp_server.sh
```

This script handles:

- Environment detection (development vs. production)
- Dependency verification
- Configuration loading
- Server initialization with appropriate parameters

### Automatic Environment Detection

The startup script automatically detects the environment:

1. In local development environments, it will use the standard startup method
2. In production environments, it will use systemd service management

## Cursor IDE Integration

For Cursor IDE development:

1. The MCP server can be started from the integrated terminal
2. Cursor's AI features can be used to navigate and understand the MCP codebase
3. Debugging and testing can be performed directly within the IDE

To set up the MCP server in Cursor:

1. Open the repository in Cursor
2. Open the integrated terminal (Ctrl+`)
3. Run the startup script:
   ```bash
   ./mcp_server/scripts/start_mcp_server.sh
   ```

## CI/CD Integration

The MCP server includes GitHub Actions workflows for continuous integration and deployment:

1. Automated testing on pull requests
2. Deployment to staging environments
3. Production deployment with approval gates

See `.github/workflows/deploy.yml` for the complete CI/CD configuration.

## Monitoring Integration

The MCP server includes Prometheus-compatible metrics endpoints for monitoring:

1. `/metrics` - Standard Prometheus metrics
2. `/health` - Health check endpoint

These endpoints can be integrated with monitoring systems like Grafana for visualization and alerting.

## Local Development Workflow

For local development:

1. Start the MCP server:
   ```bash
   ./mcp_server/scripts/start_mcp_server.sh
   ```

2. Verify the server is running:
   ```bash
   curl http://localhost:8000/health
   ```

3. Make changes to the code

4. Restart the server to apply changes:
   ```bash
   ./mcp_server/scripts/start_mcp_server.sh --restart
   ```

## Troubleshooting

If the MCP server fails to start:

1. Check the logs:
   ```bash
   tail -f mcp_server.log
   ```

2. Verify dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. Check configuration:
   ```bash
   cat mcp_server/config/mcp_config.json
   ```

4. Ensure ports are available:
   ```bash
   netstat -tuln | grep 8000
   ```
