# 🎼 Orchestra AI Autostart System Guide

## Overview

The Orchestra AI Autostart System ensures all necessary scripts and services are automatically running, including:
- AI context updates
- API server
- Frontend server
- MCP memory server
- System monitoring
- Health checks

## Quick Start

### 1. Install the Autostart System

```bash
# Make scripts executable
chmod +x scripts/orchestra_autostart.py
chmod +x scripts/install_autostart.sh

# Install as system service
./scripts/install_autostart.sh
```

### 2. Manual Run (for testing)

```bash
# Run directly
./orchestra-autostart

# Or with Python
python scripts/orchestra_autostart.py
```

## Configuration

The autostart system uses `orchestra_autostart.json` for configuration:

```json
{
  "services": {
    "ai_context": {
      "name": "AI Context Loader",
      "command": "python scripts/setup_ai_agents.py --update-context",
      "type": "oneshot",      // Runs once at startup
      "enabled": true,
      "priority": 1           // Lower number = higher priority
    },
    "api": {
      "name": "API Server",
      "command": "./start_api.sh",
      "type": "daemon",       // Continuous service
      "enabled": true,
      "priority": 2,
      "health_check": "http://localhost:8000/health",
      "startup_delay": 3      // Wait 3 seconds after starting
    },
    // ... more services
  }
}
```

### Service Types

- **`oneshot`**: Runs once at startup (e.g., setup scripts)
- **`daemon`**: Continuous services that should always be running
- **`periodic`**: Services that run on a schedule (handled by cron)

## Features

### 1. **Dependency Checking**
- Verifies Python 3.11+
- Checks for virtual environment
- Validates Node.js and npm
- Confirms Docker installation

### 2. **Port Management**
- Checks if required ports are available
- Reports conflicts before starting services
- Ports monitored: 8000, 3000, 8003, 5432, 6379

### 3. **Health Monitoring**
- HTTP health checks for services
- Automatic restart on failure
- Configurable retry policies

### 4. **Process Management**
- Graceful shutdown on SIGTERM/SIGINT
- Process group management
- Clean subprocess handling

## System Integration

### macOS (LaunchAgent)

The system installs as a LaunchAgent that:
- Starts automatically on login
- Restarts on crash
- Logs to `logs/autostart-*.log`

**Commands:**
```bash
# Start service
launchctl start com.orchestra.ai.autostart

# Stop service
launchctl stop com.orchestra.ai.autostart

# Check status
launchctl list | grep orchestra

# View logs
tail -f logs/autostart-*.log
```

### Linux (systemd)

The system installs as a systemd service that:
- Starts automatically on boot
- Restarts on failure
- Integrates with journald

**Commands:**
```bash
# Start service
sudo systemctl start orchestra-ai-autostart

# Stop service
sudo systemctl stop orchestra-ai-autostart

# Check status
sudo systemctl status orchestra-ai-autostart

# View logs
sudo journalctl -u orchestra-ai-autostart -f
```

## Adding New Services

To add a new service to autostart:

1. Edit `orchestra_autostart.json`
2. Add your service configuration:

```json
"my_service": {
  "name": "My New Service",
  "command": "./start_my_service.sh",
  "type": "daemon",
  "enabled": true,
  "priority": 5,
  "health_check": "http://localhost:8080/health",
  "startup_delay": 2
}
```

3. Restart the autostart manager

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   tail -f logs/autostart.log
   ```

2. Verify dependencies:
   ```bash
   python scripts/orchestra_autostart.py --check-deps
   ```

3. Check port availability:
   ```bash
   lsof -i :8000  # Check specific port
   ```

### Service Keeps Crashing

1. Check service-specific logs
2. Verify environment variables
3. Test service manually:
   ```bash
   ./start_api.sh  # Run directly to see errors
   ```

### Permission Issues

- Ensure scripts are executable: `chmod +x scripts/*.sh`
- Check file ownership
- Verify virtual environment permissions

## Environment Variables

The autostart system sets these environment variables:

- `PYTHONPATH`: Project and API paths
- `ORCHESTRA_AI_ENV`: Development/production mode
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `NODE_ENV`: Node.js environment

## Monitoring

The system includes automatic monitoring that:
- Checks service health every 30 seconds
- Restarts failed services
- Logs all events
- Tracks restart attempts

## Best Practices

1. **Always use health checks** for daemon services
2. **Set appropriate startup delays** to avoid race conditions
3. **Use priority levels** to ensure proper startup order
4. **Monitor logs** regularly for issues
5. **Test services manually** before adding to autostart

## Integration with AI Agents

The autostart system ensures AI agents always have:
- Updated context via `setup_ai_agents.py`
- Running API endpoints
- Available MCP servers
- Fresh project metadata

This means you can rely on these services being available whenever your AI coding agents need them.

## Security Considerations

- Services run as your user (not root)
- No elevated privileges required
- Logs are user-readable only
- Environment variables are isolated

## Uninstalling

To remove the autostart system:

### macOS
```bash
launchctl unload ~/Library/LaunchAgents/com.orchestra.ai.autostart.plist
rm ~/Library/LaunchAgents/com.orchestra.ai.autostart.plist
```

### Linux
```bash
sudo systemctl stop orchestra-ai-autostart
sudo systemctl disable orchestra-ai-autostart
sudo rm /etc/systemd/system/orchestra-ai-autostart.service
sudo systemctl daemon-reload
``` 