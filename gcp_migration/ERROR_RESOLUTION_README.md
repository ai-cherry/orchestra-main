# AI Orchestra Migration Error Resolution Toolkit

This toolkit provides comprehensive tools for diagnosing, resolving, and documenting critical errors encountered during the Google Cloud Platform migration process.

## Overview

The migration error resolution toolkit includes the following components:

1. **MCP Server Diagnostics** - A comprehensive tool for diagnosing MCP server issues
2. **Migration Error Resolver** - A tool that identifies and resolves critical migration errors
3. **Migration Error Manager** - A wrapper script that orchestrates the entire error resolution process
4. **Incident Report Templates** - Templates for documenting migration incidents and their resolution

## Prerequisites

- Python 3.8+
- Bash shell environment
- Access to the MCP server (local or remote)
- Appropriate permissions to access logs and restart services

## Components

### MCP Server Diagnostics (`mcp_server_diagnostics.py`)

A comprehensive diagnostics tool for the MCP server, supporting the following operations:

- Service status checks
- Port availability checks
- Log file analysis
- Configuration validation
- Data directory verification
- Network connectivity testing
- Common issue repair
- Incident report generation

#### Usage

```bash
./mcp_server_diagnostics.py --diagnostics
```

**Options:**

- `--service NAME` - MCP service name (default: mcp-server)
- `--log-dir DIR` - Log directory (default: /var/log/mcp)
- `--port NUM` - MCP server port (default: 8080)
- `--config-dir DIR` - Configuration directory (default: /etc/mcp)
- `--data-dir DIR` - Data directory (default: /var/lib/mcp)
- `--check-status` - Check service status only
- `--check-port` - Check port availability only
- `--check-logs` - Check logs for errors only
- `--check-config` - Check configuration files only
- `--check-data` - Check data directory only
- `--check-network` - Check network connectivity only
- `--repair` - Attempt to repair common issues
- `--diagnostics` - Run full diagnostics
- `--report` - Create incident report
- `--report-file FILE` - Specify incident report output file
- `--json` - Output in JSON format
- `--verbose` - Verbose output

### Resolution Tool (`resolve_migration_errors.py`)

A tool that identifies and resolves critical errors encountered during the migration process:

- Parses migration logs for critical errors
- Checks MCP server status
- Attempts to repair issues
- Verifies data integrity post-repair
- Generates comprehensive incident reports

#### Usage

```bash
./resolve_migration_errors.py --all
```

**Options:**

- `--log-path PATH` - Path to migration log file
- `--log-dir DIR` - Log directory (default: /var/log/mcp)
- `--report-dir DIR` - Incident report directory (default: incidents)
- `--service NAME` - MCP service name (default: mcp-server)
- `--check` - Check for critical errors
- `--repair` - Attempt to repair issues
- `--verify` - Verify data integrity
- `--report` - Generate incident report
- `--all` - Run all actions
- `--json` - Output in JSON format
- `--verbose` - Verbose output

### Migration Error Manager (`migration_error_manager.sh`)

A shell script that orchestrates the entire error resolution process:

1. Checks for required tools
2. Runs diagnostics on the MCP server
3. Parses logs for critical errors
4. Attempts to repair identified issues
5. Verifies data integrity post-repair
6. Generates an incident report

#### Usage

```bash
./migration_error_manager.sh
```

**Options:**

- `--log-dir=DIR` - Log directory (default: /var/log/mcp)
- `--incident-dir=DIR` - Incident report directory (default: incidents)
- `--service=NAME` - MCP service name (default: mcp-server)
- `--no-repair` - Skip repair attempts
- `--no-verify` - Skip data integrity verification
- `--no-report` - Skip incident report generation
- `--verbose` - Enable verbose output
- `--help` - Show help message

## Directory Structure

```
gcp_migration/
├── mcp_server_diagnostics.py    # MCP server diagnostics tool
├── resolve_migration_errors.py  # Migration error resolver
├── migration_error_manager.sh   # Orchestration script
├── templates/                   # Templates directory
│   └── incident_report_template.md  # Incident report template
└── incidents/                   # Generated incident reports
```

## Common Error Patterns and Resolutions

### Connection Issues

**Symptoms:**
- "Connection refused" errors in logs
- MCP server not running
- Port conflicts

**Resolution:**
```bash
./migration_error_manager.sh --verbose
```

### Permission Errors

**Symptoms:**
- "Permission denied" in logs
- Unable to access data or config files

**Resolution:**
```bash
# Check directory permissions
ls -la /var/lib/mcp
ls -la /etc/mcp

# Fix permissions if needed
sudo chmod -R 755 /var/lib/mcp
```

### Configuration Issues

**Symptoms:**
- Invalid configuration file formats
- Missing required configuration parameters

**Resolution:**
```bash
# Run diagnostics with config check
./mcp_server_diagnostics.py --check-config --verbose
```

## Incident Report Generation

The toolkit automatically generates detailed incident reports including:

- Summary of the incident
- Critical issues identified
- Repair actions taken
- Data integrity verification results
- Recommendations for next steps

Reports are saved in the `incidents` directory by default.

## Integration with Deployment Process

To integrate the error resolution toolkit with your deployment process:

```bash
# Add to your deployment script
deploy_to_gcp() {
    # Deployment code here...
    
    # Check for errors after deployment
    if [ $? -ne 0 ]; then
        echo "Deployment encountered errors. Running error resolution..."
        ./gcp_migration/migration_error_manager.sh
    fi
}
```

## Best Practices

1. **Always check logs first:** Many issues can be identified through log analysis
2. **Verify MCP server status:** The MCP server is critical for migration
3. **Generate incident reports:** Keep a record of all issues and their resolution
4. **Verify data integrity:** Always verify data integrity after making repairs
5. **Use the orchestration script:** The migration_error_manager.sh provides a comprehensive approach

## Troubleshooting

If the error resolution toolkit itself encounters issues:

1. Check permissions (scripts need to be executable)
2. Verify Python 3.8+ is installed
3. Ensure log directories exist and are accessible
4. Run with `--verbose` flag for detailed output

For further assistance, consult the AI Orchestra support team or check the migration documentation.