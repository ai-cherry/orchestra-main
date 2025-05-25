# Phidata with PostgreSQL/PGVector Integration

This document provides a comprehensive guide to setting up and using Phidata with PostgreSQL/PGVector for Orchestra. This integration enables high-performance vector embedding storage and retrieval for AI agents.

## Overview

The integration consists of:

- **CloudSQL PostgreSQL** with pgvector extension for storing vector embeddings
- **Phidata Agent Wrapper** with native PostgreSQL storage capabilities
- **VertexAI embeddings** integration for high-quality vector representations
- **Deployment infrastructure** defined in Terraform

## Prerequisites

- Google Cloud Platform (GCP) account with appropriate permissions
- Terraform installed (or use our Docker-based setup)
- Python 3.8+ with pip
- Google Cloud CLI (gcloud) configured with your project

## Setup Guide

### Step 1: Environment Configuration

First, set up your environment variables. We've created a template in `.env.postgres` with the necessary variables:

```bash
# Source the environment variables
source .env.postgres
```

Variables include:

- `GCP_PROJECT_ID` - Your Google Cloud project ID
- `GCP_REGION` - Region for deployment (e.g., us-central1)
- `CLOUD_SQL_INSTANCE_CONNECTION_NAME` - Cloud SQL connection string
- `CLOUD_SQL_DATABASE` - Database name (usually phidata_memory)
- `CLOUD_SQL_USER` - Database user
- `CLOUD_SQL_PASSWORD_SECRET_NAME` - Secret name for the password

### Step 2: Install Dependencies

We've provided a script to install all required dependencies:

```bash
./install_phidata_deps.sh
```

This installs:

- Phidata agent framework
- SQLAlchemy and PostgreSQL drivers
- Google Cloud libraries
- PGVector support packages

### Step 3: Infrastructure Provisioning

The infrastructure is defined in Terraform files in `infra/orchestra-terraform/`. Use our script to provision it:

```bash
./run_terraform_dev.sh
```

This creates:

- Cloud SQL PostgreSQL instance with pgvector extension
- Service accounts with proper permissions
- Secret Manager secrets for secure password management
- Cloud Run service with CloudSQL proxy

### Step 4: PostgreSQL Schema Setup

Once infrastructure is provisioned, set up the database schema:

```bash
python scripts/setup_postgres_pgvector.py --apply --schema llm
```

This creates:

- Required database tables
- PGVector extension
- Optimized indexes for vector search

### Step 5: Agent Registration

An example is provided to register a Phidata agent with PostgreSQL storage:

```bash
python examples/register_phidata_postgres_agent.py
```

### Step 6: Verification

Use our verification tools to ensure everything is set up correctly:

```bash
# Verify overall setup
./verify_phidata_setup.py

# Test PostgreSQL connection
./test_postgres_connection.py
```

## Integration Tests

After setup, run the integration tests to verify that everything works:

```bash
# LLM integration
python -m packages.llm.src.test_phidata_integration

# Tool integration
python -m packages.tools.src.test_phidata_integration
```

## Components

### PhidataAgentWrapper

The `PhidataAgentWrapper` in `updated_phidata_wrapper.py` provides:

- Native PostgreSQL storage for agent history
- PGVector integration for embeddings
- Support for both single agents and teams
- Conversion between Orchestra and Phidata formats

### CloudSQL PGVector Module

The `cloudsql_pgvector.py` module provides:

- Connection handling to Cloud SQL with either IAM or password auth
- PgVector2 configuration for storing embeddings
- PgAssistantStorage for storing agent conversation history
- VertexAiEmbedder integration for creating embeddings

### Setup Scripts

- `setup_postgres_pgvector.py`: Configures the PostgreSQL database with pgvector
- `install_phidata_deps.sh`: Installs all required dependencies
- `verify_phidata_setup.py`: Verifies your setup is correct
- `test_postgres_connection.py`: Tests PostgreSQL connectivity

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐
│                 │     │                     │
│  Orchestra API  │────►│  PhidataAgentWrapper│
│                 │     │                     │
└────────┬────────┘     └──────────┬──────────┘
         │                         │
         │                         ▼
         │              ┌─────────────────────┐
         │              │                     │
         └──────────────►  Cloud SQL PGVector │
                        │                     │
                        └─────────────────────┘
```

## Best Practices

1. **Security**: Always use IAM authentication when possible for better security
2. **Scalability**: Use partitioning by agent_id for improved performance
3. **Monitoring**: Set up CloudSQL monitoring for database performance
4. **Backup**: Enable point-in-time recovery and regular backups
5. **Testing**: Always run the verification tests after setup

## Troubleshooting

### Connection Issues

If you encounter connection issues:

- Check that the Cloud SQL instance is running
- Verify IAM permissions are correct
- Ensure the Cloud SQL proxy is running if testing locally
- Verify environment variables are set correctly

### Extension Issues

If pgvector extension is not working:

- Verify PostgreSQL version (must be 12+ for pgvector)
- Run the setup script with `--apply` flag
- Check for errors in the PostgreSQL logs

### Embedding Issues

If embeddings are not working correctly:

- Verify the VertexAI embedding model is available
- Check API permissions for the service account
- Ensure the vector dimension matches the model output (768 for gecko-003)

## Resources

- [Phidata Documentation](https://docs.phidata.com)
- [PGVector GitHub](https://github.com/pgvector/pgvector)
- [Google Cloud SQL Documentation](https://cloud.google.com/sql/docs/postgres)
- [Terraform Documentation](https://www.terraform.io/docs)
