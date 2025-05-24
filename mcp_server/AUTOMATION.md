# MCP Server Automation Guide

This document explains how to set up the MCP memory system to run automatically on startup or after rebuilding your environment.

## Automation Options

The MCP memory system provides several automation options:

1. **VS Code Tasks** - Automatic startup in VSCode
2. **Systemd Service** - For Linux systems with systemd
3. **Docker Container** - Containerized deployment
4. **Manual Script** - Universal startup script

## 1. VS Code Tasks

The `.vscode/tasks.json` file includes a task to automatically start the MCP server when you open the project folder in VS Code:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start MCP Server",
      "type": "shell",
      "command": "${workspaceFolder}/mcp_server/scripts/start_mcp_server.sh",
      "runOptions": {
        "runOn": "folderOpen"
      }
    }
  ]
}
```

This task runs automatically when you open the project in VS Code. You can also run it manually:

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Type "Tasks: Run Task"
3. Select "Start MCP Server"

## 2. Systemd Service

For Linux systems with systemd, you can install the MCP server as a system service:

```bash
sudo ./mcp_server/scripts/install_mcp_service.sh
```

This will:

- Install the MCP package
- Create a systemd service
- Enable autostart on system boot
- Start the service

### Manual Service Management

Once installed, you can manage the service with standard systemd commands:

```bash
# Check service status
systemctl status mcp-server.service

# Start the service
systemctl start mcp-server.service

# Stop the service
systemctl stop mcp-server.service

# Restart the service
systemctl restart mcp-server.service

# Enable autostart on boot
systemctl enable mcp-server.service

# Disable autostart
systemctl disable mcp-server.service

# View logs
journalctl -u mcp-server.service -f
```

## 3. Docker Container

For Docker environments, use the provided Dockerfile and docker-compose.yml:

```bash
# Navigate to the scripts directory
cd mcp_server/scripts

# Start with docker-compose (builds and runs)
docker-compose up -d

# Stop the container
docker-compose down

# View logs
docker-compose logs -f
```

The Docker setup includes:

- Automatic restart on container crash
- Volume for persistent data storage
- Port exposure (8080)
- Environment variable support for configuration

### Docker Rebuild

To rebuild the container after code changes:

```bash
docker-compose up -d --build
```

## 4. Universal Startup Script

For any environment, you can use the universal startup script:

```bash
./mcp_server/scripts/start_mcp_server.sh
```

This script:

- Detects your environment (Docker, Codespace, systemd, or standard)
- Uses the appropriate method to start the server
- Installs dependencies if needed
- Creates configuration if missing
- Ensures only one instance is running

## GitHub Codespaces Integration

For GitHub Codespaces:

1. The VS Code task will automatically start the server when opening the codespace
2. The startup script will detect Codespaces and use the direct run method
3. The server will run in the background

## Environment Detection

The startup script automatically detects your environment:

- **Docker container**: Uses direct run method
- **GitHub Codespace**: Uses direct run method
- **System with systemd**: Uses the systemd service
- **Other environments**: Uses direct run method with background process

## Troubleshooting

If the MCP server fails to start:

1. Check the logs:

   - Direct run: `/tmp/mcp-server.log`
   - Systemd: `journalctl -u mcp-server.service -f`
   - Docker: `docker-compose logs -f`

2. Common issues:

   - Port 8080 already in use
   - Missing dependencies
   - Permission issues in systemd service
   - Configuration file errors

3. Manual start for debugging:
   ```bash
   python -m mcp_server.main --config mcp_server/config.json
   ```

## Automatic Restart on Crashes

- **Systemd**: The service is configured to restart automatically on crashes
- **Docker**: The container has `restart: always` set
- **Direct run**: Use a tool like `supervisor` or `pm2` for crash recovery
