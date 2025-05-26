# Orchestra Production Deployment Guide

This guide provides a comprehensive overview of the deployment process for Orchestra to production environments. It details the steps involved, scripts available, and recommendations for a successful deployment.

## Table of Contents

- [Overview](#overview)
- [Deployment Scripts](#deployment-scripts)
- [Pre-Deployment Verification](#pre-deployment-verification)
- [Setting Up Production Environment](#setting-up-production-environment)
- [Production Deployment](#production-deployment)
- [Post-Deployment Verification](#post-deployment-verification)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Cleanup Plan](#cleanup-plan)
- [Troubleshooting](#troubleshooting)

## Overview

Deploying Orchestra to production involves several steps to ensure a reliable, secure, and well-monitored environment. The process follows a dev → prod progression to minimize risks:

1. Develop and test in a development environment
2. Verify the system works as expected with pre-deployment checks
3. Set up production infrastructure and configurations
4. Deploy to production
5. Verify the production deployment
6. Set up monitoring and alerting
7. Follow the cleanup plan to remove deprecated code

## Architecture Overview

Orchestra uses a two-service deployment architecture:

1. **Orchestra API Service** (`orchestrator-api-{env}`):

   - Primary backend service implementing the Orchestra orchestration logic
   - Provides API endpoints for agent interaction, including the `/phidata/chat` endpoint
   - Connects to PostgreSQL and Redis for data persistence and caching
   - Manages LLM provider integration, agent coordination, and memory systems

2. **Phidata Agent UI Service** (`phidata-agent-ui-{env}`):
   - Frontend UI service using the official Phidata Agent UI container image (`phidata/agent_ui:1.0.0`)
   - Serves as a placeholder UI for interacting with the Orchestra backend
   - Connects to the Orchestra API using the `PHIDATA_API_URL` environment variable
   - Runs as a separate Cloud Run service without direct access to databases or LLMs

This separation of concerns allows for:

- Independent scaling of frontend and backend services
- Use of the standard Phidata UI container without customization
- Clear API contract between frontend and backend
- Future replacements of either component without affecting the other

Both services are deployed together using Terraform or the Cloud Run deployment method.

## Deployment Scripts

We've created several scripts to automate and streamline the deployment process:

1. **`run_pre_deployment_automated.sh`**

   - Automates pre-deployment verification
   - Checks environment readiness
   - Runs integration tests and diagnostics

2. **`scripts/setup_prod_secrets.sh`**

   - Sets up production secrets in Google Secret Manager
   - Creates or updates required secrets for production
   - Configures IAM permissions for service accounts

3. **`deploy_to_production.sh`**
   - Orchestrates the full production deployment process
   - Guides you through all necessary steps
   - Handles Terraform workspace and configuration

## Pre-Deployment Verification

Before deploying to production, it's crucial to verify that your system is ready:

```bash
./run_pre_deployment_automated.sh
```

This script checks:

- Deployment readiness
- PostgreSQL setup with pgvector extensions
- Credentials validity
- System diagnostics
- Integration tests (Firestore, Redis, PostgreSQL, LLM)
- UI validation

Review the output carefully and fix any issues before proceeding to production deployment.

## Setting Up Production Environment

### 1. Production Terraform Configuration

We've created a production configuration file at `infra/prod.tfvars` with appropriate settings:

```hcl
# Key production settings
env = "prod"
region = "us-central1"
cloud_run_min_instances = 2
cloud_run_max_instances = 20
cloudsql_machine_type = "db-custom-4-8192"
cloudsql_disk_size = 50  # GB
use_private_endpoints = true
enable_cloud_armor = true
enable_alerting = true
```

Review and modify this file to match your production requirements.

### 2. Production Secrets

Set up production secrets securely using:

```bash
./scripts/setup_prod_secrets.sh
```

This script helps you create and manage:

- API keys (OpenRouter, Portkey)
- Database passwords
- Redis credentials
- Other sensitive information

The secrets are stored in Google Secret Manager with proper IAM permissions.

## Production Deployment

When you're ready to deploy to production, use:

```bash
./deploy_to_production.sh
```

This script guides you through:

1. Verifying prerequisites
2. Running pre-deployment checks (if not already done)
3. Setting up production secrets (if not already done)
4. Reviewing production configuration
5. Deploying using Terraform
6. Verifying the deployment
7. Setting up monitoring and alerts

The script implements safeguards to ensure a smooth deployment process and avoid common mistakes.

## Post-Deployment Verification

After deployment, verify both services:

1. **API Health**: Check if the API is responding correctly

   ```bash
   curl $(gcloud run services describe orchestrator-api-prod --region=us-central1 --format="value(status.url)")/api/health
   ```

2. **Phidata UI**: Verify the UI is accessible

   ```bash
   # Get the UI service URL
   UI_URL=$(gcloud run services describe phidata-agent-ui-prod --region=us-central1 --format="value(status.url)")
   echo $UI_URL
   ```

   - Visit this URL in your web browser to confirm the Phidata Agent UI is working
   - Test sending messages through the UI to verify it connects to the Orchestra API

3. **Logs**: Review recent logs for any errors

   ```bash
   # API logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-prod" --limit=10

   # UI logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=phidata-agent-ui-prod" --limit=10
   ```

4. **Connectivity**: Verify the UI service is successfully connecting to the API by checking for successful request logs in the API service when using the UI

## Monitoring and Alerting

The deployment script sets up basic monitoring and alerting for:

1. **High Error Rate**: Alerts if the error rate exceeds a threshold
2. **High Latency**: Alerts if API latency exceeds acceptable limits

For more advanced monitoring:

1. Open the Google Cloud Console
2. Navigate to Monitoring → Dashboards
3. Create custom dashboards for Orchestra metrics
4. Set up additional alerting policies as needed

## Cleanup Plan

After successful production deployment, follow the prioritized cleanup plan:

### Priority 1 (Safest)

- Remove redundant diagnostic scripts
  - `diagnose_environment.py`
  - `diagnose_orchestrator.py`
  - `diagnose_patrick_issues.py`
- Remove older setup scripts
  - `setup.sh`
  - `setup_gcp_auth.sh`

### Priority 2 (Requires Care)

- Remove `future/firestore_memory_manager.py` after validating the V2 adapter works correctly

### Priority 3 (Requires Care)

- Remove redundant agent wrapper files (`updated_phidata_wrapper.py`) after confirming all code uses the official implementation

### Priority 4 (Ongoing)

- Refactor shared utilities
- Standardize configurations
- Update documentation

## Troubleshooting

### Common Issues

1. **API Key Errors**

   - Check Secret Manager for proper key storage
   - Verify IAM permissions are correctly set

2. **Database Connection Issues**

   - Check network connectivity (VPC settings)
   - Verify IP allowlisting is configured correctly
   - Check service account permissions

3. **Deployment Failures**
   - Review Terraform logs for detailed error information
   - Check Cloud Build logs if using CI/CD

### Getting Help

If you encounter issues:

1. Check the logs for specific error messages
2. Review the [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md)
3. Look for similar issues in [Orchestra Deployment Steps](./ORCHESTRA_DEPLOYMENT_STEPS.md)

## Conclusion

By following this guide and using the provided scripts, you can deploy Orchestra to production with confidence. The automated verification, configuration management, and monitoring setup help ensure a reliable and maintainable production environment.

Remember to:

1. Test thoroughly in development first
2. Review configuration before applying
3. Monitor the production deployment closely
4. Follow the cleanup plan after successful deployment
