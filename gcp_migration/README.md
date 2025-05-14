# AI Orchestra GCP Migration Framework

This directory contains the unified framework for migrating AI Orchestra to Google Cloud Platform. The framework provides a structured, phased approach to migration with built-in checkpointing, validation, and reporting.

## Key Components

### 1. Unified Client Libraries

| Component | Description |
|-----------|-------------|
| [`mcp_client_unified.py`](./mcp_client_unified.py) | Unified MCP client with comprehensive error handling, connection pooling, and async support |
| [`circuit_breaker_unified.py`](./circuit_breaker_unified.py) | Thread-safe circuit breaker implementation for resilient service communication |

### 2. Migration Execution Framework

| Component | Description |
|-----------|-------------|
| [`execute_unified_migration.py`](./execute_unified_migration.py) | Core migration executor with phased approach and checkpointing |
| [`run_unified_migration.sh`](./run_unified_migration.sh) | User-friendly script for running migrations with various options |

### 3. Validation Tools

| Component | Description |
|-----------|-------------|
| [`validate_migration.py`](./validate_migration.py) | Toolset for validating migration success with specific test cases |
| [`MIGRATION_MONITORING_README.md`](./MIGRATION_MONITORING_README.md) | Documentation for ongoing monitoring of migrated infrastructure |

## Migration Phases

The migration process is broken down into these phases:

1. **Initialization**: Environment detection, authentication validation, and dependency checking
2. **Infrastructure**: Setting up core GCP infrastructure, workstations, and security configuration
3. **Database**: Setting up AlloyDB instances, schema migration, and data migration
4. **Vector Search**: Creating and optimizing vector indices with circuit breaker patterns
5. **APIs**: Deploying and configuring API services
6. **Validation**: Comprehensive testing of connectivity, performance, and security
7. **Finalization**: Cleanup, documentation updates, and report generation

## How to Use

### Basic Usage

To run a full migration:

```bash
./run_unified_migration.sh --full
```

To run a specific component:

```bash
./run_unified_migration.sh --component vector-index-creation
```

To run validation only:

```bash
./run_unified_migration.sh --validate
```

To resume from a checkpoint:

```bash
./run_unified_migration.sh --resume
```

### Advanced Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Simulate migration without making changes |
| `--env ENV` | Set environment (`development`, `staging`, `production`) |
| `--force` | Skip prerequisite checks |
| `--debug` | Enable verbose debug logging |
| `--checkpoint PATH` | Specify custom checkpoint file path |

## Improvements Over Previous Implementations

This unified migration framework addresses several issues found in previous migration attempts:

1. **Code Consistency**: Standardized error handling, logging, and naming conventions across components
2. **Checkpointing**: Ability to resume interrupted migrations from last successful step
3. **Thread Safety**: Properly synchronized access to shared resources
4. **Exception Context Preservation**: Original exceptions are preserved for better debugging
5. **Environment Detection**: Automatic detection of execution environment
6. **Connection Pooling**: Optimized connection management for better performance
7. **Comprehensive Validation**: Detailed validation with clear pass/fail criteria
8. **Detailed Reporting**: Comprehensive reports with metrics and recommendations

## Validation Criteria

A successful migration must meet these criteria:

1. Project correctly assigned to organization `873291114285`
2. Workstation cluster "ai-development" exists with GPU support
3. AlloyDB cluster "agent-storage" exists and is accessible
4. Redis instance "agent-memory" exists and is accessible 
5. Vector search latency < 30ms
6. API response time < 100ms
7. Workstation startup time < 3 minutes

## Architecture

The migration framework follows a modular design:

```
┌─────────────────────┐
│                     │
│  Migration Executor │
│                     │
└───────────┬─────────┘
            │
            ▼
┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │
│   Phase Execution   │◄───►│  Component Registry │
│                     │     │                     │
└───────────┬─────────┘     └─────────────────────┘
            │
            ▼
┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │
│ Component Execution │◄───►│ Checkpointing System│
│                     │     │                     │
└───────────┬─────────┘     └─────────────────────┘
            │
            ▼
┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │
│  Unified Libraries  │◄───►│  Validation System  │
│                     │     │                     │
└─────────────────────┘     └─────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure your `PYTHONPATH` includes the project root directory
2. **Authentication Failures**: Ensure you have valid GCP credentials
3. **Dependency Errors**: Run the dependency check or install required packages
4. **Permission Issues**: Verify the service account has required permissions
5. **Network Issues**: Check firewall settings and network connectivity

### Debugging

For detailed debugging, run with the `--debug` flag:

```bash
./run_unified_migration.sh --debug --full
```

Logs are written to both standard output and `migration_execution.log`.

## Contributing

When adding new components or modifying existing ones:

1. Follow the established naming and error handling patterns
2. Add appropriate validation steps
3. Update the documentation
4. Ensure backward compatibility with checkpoints
