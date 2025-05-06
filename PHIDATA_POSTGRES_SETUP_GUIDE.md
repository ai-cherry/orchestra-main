# Phidata PostgreSQL/PGVector Integration Setup Guide

This guide provides step-by-step instructions for setting up the Phidata integration with PostgreSQL and PGVector for the Orchestra environment. This integration enables efficient vector embedding storage and retrieval for AI agents.

## Prerequisites

- Google Cloud Platform (GCP) account with appropriate permissions
- GCP project with enabled APIs:
  - Cloud SQL Admin API
  - Secret Manager API
  - Vertex AI API (for embeddings)
- Service account with appropriate roles:
  - Cloud SQL Admin
  - Secret Manager Secret Accessor
  - Vertex AI User
- Terraform installed or Docker (for the dockerized Terraform approach)
- Python 3.8+

## Phase 1: Environment Setup and Configuration

### 1.1 Configure Environment Variables

Create or update the `.env.postgres` file with the following variables:

```bash
# PostgreSQL Setup Environment Variables
# GCP region (e.g., 'us-central1')
GCP_REGION=us-central1

# Format: project:region:instance
CLOUD_SQL_INSTANCE_CONNECTION_NAME=your-project:us-central1:orchestra-postgres

# Database name (e.g., 'phidata')
CLOUD_SQL_DATABASE=phidata

# Database user (e.g., 'postgres')
CLOUD_SQL_USER=postgres

# Set to 'true' to use IAM auth, default is 'false'
CLOUD_SQL_USE_IAM_AUTH=false

# Name of the secret in Secret Manager containing the password
CLOUD_SQL_PASSWORD_SECRET_NAME=cloudsql-postgres-password
```

Export these variables to your environment:

```bash
export $(grep -v '^#' .env.postgres | xargs)
```

### 1.2 Install Required Dependencies

Install all necessary Python packages:

```bash
# Install core packages
pip install phidata sqlalchemy>=2.0.0

# Install PostgreSQL-specific packages
pip install pg8000 psycopg2-binary

# Install Google Cloud packages
pip install google-cloud-secret-manager cloud-sql-python-connector
```

Alternatively, use the provided script:

```bash
./install_phidata_deps.sh
```

### 1.3 Verify Dependencies and Configuration

Run the following script to verify that all dependencies are installed and environment variables are set correctly:

```bash
python test_postgres_connection.py
```

## Phase 2: Infrastructure Provisioning

### 2.1 Provision Infrastructure with Terraform

Navigate to the Terraform directory and initialize:

```bash
cd infra/orchestra-terraform
terraform init
```

Select the dev workspace and plan:

```bash
terraform workspace select dev
terraform plan -var="env=dev"
```

Apply the Terraform configuration to create resources:

```bash
terraform apply -var="env=dev" -auto-approve
```

Alternatively, use the provided script (requires Docker):

```bash
./run_terraform_dev.sh
```

### 2.2 Get Connection Details

After Terraform provision, retrieve the Cloud SQL connection details:

```bash
cd infra/orchestra-terraform
terraform output -json > terraform_output.json
```

Update your `.env.postgres` file with the actual values from the Terraform output.

## Phase 3: Database Schema Configuration

### 3.1 Set Up PostgreSQL Schema with PGVector

Run the setup script to create the schema, tables, and pgvector extension:

```bash
python scripts/setup_postgres_pgvector.py --apply --schema llm
```

This will:
1. Connect to the provisioned Cloud SQL instance
2. Create the pgvector extension if it doesn't exist
3. Create the specified schema (e.g., "llm")
4. Configure optimal database settings for vector operations
5. Create necessary indexes for vector search

## Phase 4: Integration Testing

### 4.1 Run the Phidata Setup Verification

Verify that the Phidata setup is correctly configured:

```bash
python verify_phidata_setup.py
```

### 4.2 Test PostgreSQL Connection

Test the connection to PostgreSQL:

```bash
python test_postgres_connection.py
```

### 4.3 Run Integration Tests

Test the integration with LLM providers through Portkey:

```bash
python -m packages.llm.src.test_phidata_integration
```

Test the integration with tools:

```bash
python -m packages.tools.src.test_phidata_integration
```

## Phase 5: Agent Registration and Usage

### 5.1 Register a Phidata Agent with PostgreSQL Storage

Use the provided example to register a Phidata agent with PostgreSQL storage:

```bash
python examples/register_phidata_postgres_agent.py
```

### 5.2 Run Integration Tests for Phidata Agents

Test the Phidata agents functioning with the PostgreSQL/PGVector backend:

```bash
python -m tests.integration.phidata.test_phidata_agents_integration
```

## Troubleshooting

### Authentication Issues

If you encounter GCP authentication errors:
1. Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set to the path of your service account key
2. Verify that the service account has the necessary permissions
3. Check if the instance connection name is correct

### PostgreSQL Connection Issues

If you encounter connection issues:
1. Verify that the Cloud SQL instance is running
2. Check if the Secret Manager secret for the password exists
3. Ensure that the Cloud SQL Admin API is enabled

### PGVector Extension Issues

If pgvector is not working:
1. Check the PostgreSQL version (must be 12+)
2. Verify that the extension was created correctly
3. Check for errors in the PostgreSQL logs

## Architecture Diagram

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

## Resources

- Phidata Documentation: https://docs.phidata.com
- PGVector GitHub: https://github.com/pgvector/pgvector
- Google Cloud SQL Documentation: https://cloud.google.com/sql/docs/postgres
- Terraform Documentation: https://www.terraform.io/docs
