# AI Orchestra Agent Infrastructure Setup Guide

This document provides a comprehensive guide for setting up the AI Orchestra agent infrastructure on Google Cloud Platform (GCP). It covers the bootstrap process, infrastructure components, and best practices for secure deployment.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Bootstrap Process](#bootstrap-process)
4. [Infrastructure Components](#infrastructure-components)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Next Steps](#next-steps)

## Overview

The AI Orchestra agent infrastructure provides a robust foundation for deploying and managing AI agents with different capabilities, memory systems, and tool integrations. The infrastructure is designed to be:

- **Scalable**: Support for multiple agent types and teams
- **Flexible**: Configurable memory systems and tool integrations
- **Secure**: Integration with GCP Secret Manager and IAM
- **Observable**: Monitoring and logging for agent operations
- **Maintainable**: Centralized configuration and validation

## Prerequisites

Before running the bootstrap script, ensure you have the following:

1. **GCP Project**: Access to the `cherry-ai-project` GCP project
2. **Command Line Tools**:

   - `gcloud` CLI installed and configured
   - `terraform` CLI installed (version 1.0.0+)
   - `jq` installed for JSON processing

3. **GitHub Repository**: A GitHub repository where you'll deploy the code

## Bootstrap Process

We've created a comprehensive bootstrap script that sets up the entire infrastructure in one go. The script handles:

1. Authentication with GCP
2. Enabling necessary APIs
3. Creating Terraform state bucket
4. Setting up Secret Manager secrets
5. Configuring Workload Identity Federation for GitHub Actions
6. Initializing and applying Terraform configuration
7. Updating GitHub Actions workflow file
8. Cleaning up temporary credentials

### Running the Bootstrap Script

1. Make the script executable:

   ```bash
   chmod +x scripts/bootstrap_orchestra_infrastructure.sh
   ```

2. Run the script:

   ```bash
   ./scripts/bootstrap_orchestra_infrastructure.sh
   ```

3. Follow the prompts and confirm when asked

The script will output progress information and provide next steps at the end.

### What the Bootstrap Script Does

1. **Authentication**: Uses the provided service account key to authenticate with GCP
2. **API Enablement**: Enables all necessary GCP APIs for the project
3. **Terraform Backend**: Creates a GCS bucket for Terraform state
4. **Secret Management**: Creates initial secrets in Secret Manager
5. **Workload Identity**: Sets up Workload Identity Federation for GitHub Actions
6. **Infrastructure**: Applies Terraform configuration to create infrastructure
7. **GitHub Actions**: Updates the GitHub Actions workflow file
8. **Cleanup**: Revokes and deletes the service account key

## Infrastructure Components

The infrastructure includes the following components:

### Memory Systems

1. **Redis** (Short-term Memory):

   - Fast, in-memory storage
   - Used for active conversation context
   - TTL: 1 hour

2. **Firestore** (Mid/Long-term Memory):

   - Document database for structured data
   - Used for persistent storage
   - TTL: Configurable (1 day to 30 days)

3. **Vertex AI Vector Search** (Semantic Memory):
   - Vector database for semantic search
   - Used for knowledge retrieval
   - Dimensions: 768 (configurable)

### Secret Management

All sensitive information is stored in Secret Manager:

- API keys (OpenAI, Anthropic, etc.)
- Database credentials
- Encryption keys

### Service Accounts

1. **Agent Service Account**:

   - Used by agents to access GCP resources
   - Least privilege permissions

2. **Deployment Service Account**:
   - Used by GitHub Actions for deployment
   - Impersonated via Workload Identity Federation

### Monitoring

- Cloud Monitoring dashboard for agent metrics
- Custom metrics for agent operations
- Logging for agent activities

## Security Considerations

### Workload Identity Federation

The infrastructure uses Workload Identity Federation for GitHub Actions, which is more secure than using service account keys. This allows GitHub Actions to authenticate with GCP without storing long-lived credentials.

### Secret Management

Sensitive information is stored in Secret Manager and accessed securely by the application. The bootstrap script creates initial secrets with placeholder values, which should be updated with real values after setup.

### Service Account Keys

The bootstrap script uses a service account key for initial setup, but it's revoked and deleted after setup is complete. In production, all authentication should be done via Workload Identity Federation or other secure methods.

## Monitoring and Observability

The infrastructure includes monitoring and observability features:

1. **Cloud Monitoring Dashboard**:

   - Redis memory usage
   - Firestore operations
   - Vector search queries
   - Agent errors

2. **Logging**:

   - Structured logging for agent operations
   - Error tracking
   - Performance metrics

3. **Tracing**:
   - Request tracing across services
   - Performance analysis

## Next Steps

After running the bootstrap script, you should:

1. **Update Secrets**: Replace placeholder values in Secret Manager with real values
2. **Configure GitHub Repository**:

   - Enable GitHub Actions
   - Update repository settings for Workload Identity Federation
   - Push changes to trigger the workflow

3. **Test the Infrastructure**:

   - Run the example agent configuration
   - Verify memory systems are working
   - Check monitoring dashboards

4. **Implement Memory Backends**:

   - Implement Redis memory backend
   - Implement Firestore memory backend
   - Implement Vertex AI Vector Search backend

5. **Create Unit Tests**:
   - Test configuration validation
   - Test memory systems
   - Test agent observability

## Conclusion

The AI Orchestra agent infrastructure provides a solid foundation for building and deploying AI agents on GCP. By following this guide and using the provided bootstrap script, you can quickly set up a secure, scalable, and observable infrastructure for your agents.

For more detailed information on the agent configuration system and memory architecture, see the [Agent Infrastructure Documentation](agent_infrastructure.md).
