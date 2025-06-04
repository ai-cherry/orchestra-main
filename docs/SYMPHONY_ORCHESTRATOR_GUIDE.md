# Symphony conductor - Unified Automated System Guide

## Overview

The Symphony conductor is a comprehensive automated system that manages all cleanup, maintenance, and optimization tasks for Project Symphony without requiring manual intervention. It cherry_aites all the AI Optimization Framework components automatically in the background.

## Quick Start

### One-Command Setup

```bash
# Make setup script executable and run it
chmod +x scripts/setup_symphony_conductor.sh
./scripts/setup_symphony_conductor.sh
```

This single command will:
1. Install required dependencies
2. Set up all necessary directories
3. Create a systemd service
4. Start the conductor automatically
5. Enable it to run on system startup

## Architecture

### Core Components

1. **Symphony conductor** (`scripts/symphony_conductor.py`)
   - Central coordination engine
   - Task scheduling and dependency management
   - Health monitoring and reporting
   - Automatic retry and failure handling

2. **Automated Tasks**
   - Inventory scanning (daily at 2 AM)
   - Cleanup analysis (daily at 2:30 AM)
   - Cleanup execution (weekly on Sundays at 3 AM)
   - Health checks (every 30 minutes)
   - Automation monitoring (hourly)
   - Expired file cleanup (daily at 4 AM)
   - Git maintenance (monthly)

3. **Supporting Scripts**
   - `comprehensive_inventory.sh` - File discovery and analysis
   - `cleanup_engine.py` - Intelligent cleanup with safety checks
   - `automation_manager.py` - Script lifecycle management
   - `quick_health_check.sh` - System health monitoring

## How It Works

### Task Scheduling

The conductor uses cron-like expressions to schedule tasks:

```json
{
  "name": "inventory_scan",
  "command": "./scripts/comprehensive_inventory.sh",
  "schedule": "0 2 * * *",  // Daily at 2 AM
  "dependencies": [],
  "timeout": 1800,
  "enabled": true
}
```

### Dependency Management

Tasks can depend on other tasks. The conductor ensures dependencies are met before running a task:

```json
{
  "name": "cleanup_analysis",
  "schedule": "30 2 * * *",
  "dependencies": ["inventory_scan"],  // Runs after inventory_scan
}
```

### Automatic Retry

Failed tasks are automatically retried with configurable delays:

```json
{
  "retry_count": 3,
  "retry_delay": 300  // 5 minutes between retries
}
```

## Configuration

### Main Configuration File

Location: `config/conductor_config.json`

```json
{
  "tasks": [
    {
      "name": "task_name",
      "command": "command to execute",
      "schedule": "cron expression",
      "dependencies": ["dependency1", "dependency2"],
      "timeout": 3600,
      "retry_count": 3,
      "retry_delay": 300,
      "enabled": true
    }
  ],
  "settings": {
    "max_concurrent_tasks": 3,
    "task_history_retention_days": 30,
    "notification_webhook": "https://your-webhook-url",
    "enable_notifications": false
  }
}
```

### Schedule Format

Uses standard cron expressions:
- `"0 2 * * *"` - Daily at 2 AM
- `"*/30 * * * *"` - Every 30 minutes
- `"0 3 * * 0"` - Weekly on Sunday at 3 AM
- `"0 5 1 * *"` - Monthly on 1st at 5 AM

## Management Commands

### Service Control

```bash
# Check status
sudo systemctl status symphony-conductor

# Stop service
sudo systemctl stop symphony-conductor

# Start service
sudo systemctl start symphony-conductor

# Restart service
sudo systemctl restart symphony-conductor

# View logs
sudo journalctl -u symphony-conductor -f
```

### Manual Operations

```bash
# Check conductor status
python scripts/symphony_conductor.py status

# Run a specific task manually
python scripts/symphony_conductor.py run --task inventory_scan

# View detailed logs
tail -f logs/symphony_conductor.log
```

## Monitoring

### Log Files

- Main conductor log: `logs/symphony_conductor.log`
- Systemd log: `logs/conductor_systemd.log`
- Task-specific logs: `logs/automation/[task_name].log`
- Cleanup actions: `cleanup_actions.log`

### Health Files

- Task health status: `status/automation_health/[task_name].health`
- Format: `status:timestamp:exit_code`
- Example: `success:2025-06-02T10:00:00Z:0`

### Quick Health Check

```bash
# Run health check manually
./scripts/quick_health_check.sh

# Check specific metrics
python scripts/symphony_conductor.py status | jq '.recent_results'
```

## Task Details

### 1. Inventory Scan
- **Schedule**: Daily at 2 AM
- **Purpose**: Analyzes all files in the project
- **Output**: `cleanup_inventory.json`
- **Duration**: ~30 minutes (depends on project size)

### 2. Cleanup Analysis
- **Schedule**: Daily at 2:30 AM
- **Purpose**: Identifies files safe to remove
- **Dependencies**: Requires inventory scan
- **Output**: Report of cleanup candidates

### 3. Cleanup Execution
- **Schedule**: Weekly on Sundays at 3 AM
- **Purpose**: Removes obsolete files
- **Safety**: Maximum 50 files per run
- **Mode**: Non-interactive with safety limits

### 4. Health Check
- **Schedule**: Every 30 minutes
- **Purpose**: Monitor system health
- **Checks**: Temp files, automation status, disk space
- **Alerts**: Logs warnings if issues detected

### 5. Automation Health
- **Schedule**: Hourly
- **Purpose**: Check all registered automation scripts
- **Output**: Health report for each script

### 6. Expired Files Cleanup
- **Schedule**: Daily at 4 AM
- **Purpose**: Remove files past their expiration
- **Source**: `.cleanup_registry.json`

### 7. Git Maintenance
- **Schedule**: Monthly on 1st at 5 AM
- **Purpose**: Optimize git repository
- **Commands**: `git gc --aggressive --prune=now`

## Customization

### Adding New Tasks

1. Edit `config/conductor_config.json`
2. Add new task definition:
```json
{
  "name": "my_new_task",
  "command": "python scripts/my_script.py",
  "schedule": "0 4 * * *",
  "dependencies": [],
  "timeout": 1800,
  "enabled": true
}
```
3. Restart conductor: `sudo systemctl restart symphony-conductor`

### Modifying Schedules

1. Edit the task's `schedule` field in config
2. Restart conductor to apply changes
3. Check status to verify new schedule

### Disabling Tasks

Set `"enabled": false` for any task you want to disable temporarily.

## Troubleshooting

### Common Issues

1. **conductor not starting**
   ```bash
   # Check systemd logs
   sudo journalctl -u symphony-conductor -n 50
   
   # Check if port is in use
   sudo lsof -i :8080
   ```

2. **Task failing repeatedly**
   ```bash
   # Check task-specific log
   tail -f logs/automation/[task_name].log
   
   # Run task manually to debug
   python scripts/symphony_conductor.py run --task [task_name]
   ```

3. **High resource usage**
   ```bash
   # Reduce concurrent tasks in config
   "max_concurrent_tasks": 1
   ```

### Reset and Restart

```bash
# Stop service
sudo systemctl stop symphony-conductor

# Clear state
rm conductor_state.json
rm conductor.pid

# Clear logs (optional)
rm logs/symphony_conductor.log

# Start fresh
sudo systemctl start symphony-conductor
```

## Security Considerations

1. **File Permissions**: Ensure scripts are executable only by authorized users
2. **Cleanup Safety**: Protected patterns prevent critical file deletion
3. **Service User**: Runs as non-root user by default
4. **Audit Trail**: All actions logged with timestamps

## Performance Tuning

### Resource Limits

```json
{
  "settings": {
    "max_concurrent_tasks": 3,  // Adjust based on system resources
    "task_timeout_default": 3600  // Global timeout in seconds
  }
}
```

### Cleanup Limits

```json
{
  "name": "cleanup_execution",
  "command": "python scripts/cleanup_engine.py cleanup_inventory.json --execute --non-interactive --max-deletions 50"
}
```

## Integration with CI/CD

The conductor integrates with the GitHub Actions workflow:

1. **Weekly Reports**: Generated by GitHub Actions
2. **PR Comments**: Cleanup analysis on pull requests
3. **Artifact Storage**: Reports saved for 30 days

## Best Practices

1. **Monitor Logs Regularly**: Check logs weekly for any issues
2. **Review Cleanup Candidates**: Periodically review what's being cleaned
3. **Update Protected Patterns**: Add critical files to protection lists
4. **Test Changes**: Test configuration changes in development first
5. **Backup Before Major Cleanup**: Create backups before weekly cleanup

## Conclusion

The Symphony conductor provides a hands-off solution for maintaining code quality and cleanliness. Once set up, it runs continuously in the background, keeping your codebase optimized without manual intervention.

For additional help or customization, refer to the individual component documentation or contact the development team.