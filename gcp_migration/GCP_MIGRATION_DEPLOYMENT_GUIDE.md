# AI Orchestra GCP Migration Deployment Guide

This guide provides comprehensive instructions for deploying the AI Orchestra project to Google Cloud Platform (GCP) using the enhanced migration toolkit.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Migration Phases](#migration-phases)
6. [Usage Examples](#usage-examples)
7. [Monitoring and Reporting](#monitoring-and-reporting)
8. [Troubleshooting](#troubleshooting)
9. [Performance Considerations](#performance-considerations)
10. [Security Considerations](#security-considerations)

## Overview

The AI Orchestra GCP Migration Toolkit is designed to facilitate a smooth, reliable migration to Google Cloud Platform with comprehensive monitoring, error handling, and validation. The toolkit supports multiple phases of migration and provides detailed reporting on progress and issues.

### Key Components

- **Hybrid Configuration**: Environment-aware configuration management
- **Circuit Breaker Pattern**: Resilient service calls with metrics collection
- **Migration Monitor**: Detailed progress tracking and reporting
- **MCP Client**: Robust memory service client with connection pooling
- **Unified Executor**: Orchestrates the entire migration process

## Prerequisites

Before starting the migration, ensure you have the following prerequisites:

- Python 3.11+ installed
- Google Cloud SDK (`gcloud`) installed and configured
- Access to the target GCP project
- Required permissions:
  - `roles/owner` or equivalent permissions on the target project
  - `roles/iam.serviceAccountAdmin` for creating service accounts
  - `roles/cloudrun.admin` for deploying to Cloud Run

## Installation

The migration toolkit is included in the AI Orchestra repository. To set it up:

1. Clone the repository if you haven't already:

```bash
git clone https://github.com/your-org/ai-orchestra.git
cd ai-orchestra
```

2. Make the deployment scripts executable:

```bash
chmod +x gcp_migration/*.sh
chmod +x gcp_migration/*.py
```

3. Install required Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The migration toolkit uses a hybrid configuration system that adapts to different environments. Default configurations are created automatically during initialization, but you can customize them:

### Initialize Configuration

```bash
./gcp_migration/deploy_gcp_migration.sh --verify-only
```

This will create default configuration files in the `config` directory.

### Configuration Files

- `config/common.json`: Common settings for all environments
- `config/local.json`: Local development settings
- `config/codespaces.json`: GitHub Codespaces settings
- `config/workstation.json`: GCP Cloud Workstation settings
- `config/cloud_run.json`: Production Cloud Run settings

Example `common.json`:

```json
{
  "project_id": "cherry-ai-project",
  "created_at": "2025-05-13T03:05:00"
}
```

Example `cloud_run.json`:

```json
{
  "enable_monitoring": true,
  "enable_logging": true
}
```

## Migration Phases

The migration is divided into the following phases, which can be executed sequentially or individually:

1. **Core Infrastructure (`core_infrastructure`)**: Sets up the foundational GCP resources
   - VPC network
   - IAM roles and permissions
   - Service accounts

2. **Workstation Configuration (`workstation_config`)**: Configures Cloud Workstations for development
   - VS Code extensions
   - Authentication setup
   - Environment configuration

3. **Memory System (`memory_system`)**: Optimizes vector storage and retrieval
   - Vector database deployment
   - MCP server configuration
   - Memory service setup

4. **Hybrid Configuration (`hybrid_config`)**: Deploys environment-aware configuration
   - Configuration file generation
   - Environment detection
   - Service discovery

5. **AI Coding (`ai_coding`)**: Configures AI coding assistants
   - Vertex AI / Gemini Pro integration
   - AI coding prompts
   - Model optimization

6. **API Deployment (`api_deployment`)**: Deploys and optimizes Cloud Run services
   - Container building
   - Cloud Run deployment
   - Service configuration

7. **Validation (`validation`)**: Validates the migration against performance targets
   - Infrastructure validation
   - Service validation
   - Performance testing

## Usage Examples

### Full Migration

To execute the full migration with all phases:

```bash
./gcp_migration/deploy_gcp_migration.sh --project=your-project-id
```

### Specific Phase

To execute a specific phase only:

```bash
./gcp_migration/deploy_gcp_migration.sh --project=your-project-id --phase=memory_system
```

### Verify Only

To verify the current state without making changes:

```bash
./gcp_migration/deploy_gcp_migration.sh --project=your-project-id --verify-only
```

### Custom Configuration

To use a custom configuration directory:

```bash
./gcp_migration/deploy_gcp_migration.sh --project=your-project-id --config-dir=/path/to/config
```

### Verbose Output

For detailed logging output:

```bash
./gcp_migration/deploy_gcp_migration.sh --project=your-project-id --verbose
```

## Monitoring and Reporting

The migration toolkit includes comprehensive monitoring and reporting:

### Real-time Status

View the current migration status:

```bash
./gcp_migration/deploy_gcp_migration.sh --phase=status
```

### Migration Reports

After each migration run, a detailed report is generated in the logs directory (`logs/migration/reports/`). The latest report is always available at `logs/migration/reports/latest_report.md`.

The report includes:
- Overall migration status
- Phase-by-phase details
- Success rates
- Error messages
- Performance metrics
- Next steps

### Metrics Collection

The migration toolkit collects detailed metrics for each phase, which are stored in `logs/migration/migration_metrics.json`. These metrics include:
- Duration for each phase
- Success rates
- Resource counts
- Performance measurements

## Troubleshooting

### Common Issues

#### Authentication Errors

```
Error: Could not find default credentials
```

Solution: Run `gcloud auth login` and `gcloud auth application-default login`

#### Permission Denied

```
Error: Permission denied for operation on resource
```

Solution: Ensure your account has the required IAM permissions on the project

#### Circuit Breaker Errors

```
Circuit for service_name is open until 2025-05-13T03:15:00
```

Solution: Wait for the circuit to close or reset it manually by restarting the migration

#### Configuration Errors

```
Error: Invalid configuration section
```

Solution: Check your configuration files for correct formatting and required fields

### Logs

Detailed logs are stored in the `logs/migration` directory:
- `migration_status.json`: Current migration status
- `migration_metrics.json`: Detailed metrics
- `reports/`: Migration reports

## Performance Considerations

The migration toolkit includes several performance optimizations:

1. **Connection Pooling**: The MCP client uses connection pooling to efficiently reuse connections

2. **Circuit Breaker Pattern**: Prevents cascading failures and provides fast failure for unavailable services

3. **Caching**: The hybrid configuration system uses caching to reduce file I/O operations

4. **Async Operations**: Critical operations use asynchronous execution for better performance

For large migrations, consider:
- Increasing the recovery timeout in circuit breaker configurations
- Using a separate log directory for each run
- Executing phases individually rather than all at once

## Security Considerations

1. **Permission Management**: The toolkit uses principle of least privilege for service accounts

2. **Configuration Validation**: The enhanced configuration system includes schema validation

3. **Error Handling**: Detailed error messages are captured without exposing sensitive information

4. **Verification Mode**: Always run with `--verify-only` first to check what changes will be made

## Next Steps

After completing the migration:

1. Verify all services are running correctly in the GCP environment
2. Update your CI/CD pipelines to deploy to the new environment
3. Monitor performance and stability over the first 24-48 hours
4. Consider implementing additional optimizations based on the metrics collected

For additional assistance, contact the AI Orchestra team.