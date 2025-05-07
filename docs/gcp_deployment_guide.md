# Orchestra GCP Deployment Guide

This guide explains how to deploy the Orchestra AI system to Google Cloud Platform (GCP) using the provided infrastructure as code and CI/CD pipeline.

## Overview

The Orchestra deployment uses the following GCP services:

* **Cloud Run**: For hosting the API service
* **Firestore**: For persistent memory storage
* **Memorystore for Redis**: For caching and session management
* **Vertex AI Vector Search**: For semantic search capabilities
* **Secret Manager**: For secure credentials storage
* **Cloud Build**: For CI/CD pipeline
* **Artifact Registry**: For Docker image storage
* **VPC Network**: For secure connectivity between services
* **Cloud Monitoring**: For observability and alerting

## Prerequisites

1. A GCP project with billing enabled
2. Required APIs enabled (automatically done by Terraform)
3. Service account with appropriate permissions
4. API keys for external services (Portkey, OpenRouter, etc.)

## Deployment Architecture

![Orchestra GCP Architecture](https://storage.googleapis.com/cherry-ai-project-bucket/orchestra-architecture.png)

The architecture follows GCP best practices:
- Cloud Run services connect to Redis, Firestore, and Vertex AI
- All services operate within a custom VPC network
- Default-deny firewall rules with explicit allow rules only for required traffic
- Least-privilege service accounts for each component
- Monitoring with predefined SLOs and alerts

## Environment Setup

Three environments are supported:
- **dev**: Development environment (minimal resources)
- **stage**: Staging/testing environment
- **prod**: Production environment (optimized for performance and reliability)

## Creating Service Account for Deployment

1. Go to the IAM & Admin > Service Accounts section in the GCP Console
2. Create a new service account `cherrybaby-deploy`
3. Grant the necessary roles:
   - Cloud Run Admin
   - Cloud Build Editor
   - Storage Admin
   - Secret Manager Admin
   - Service Account User
   - Compute Admin
   - Artifact Registry Admin
   - Firestore Admin
   - Redis Admin
   - Vertex AI Admin

4. Create and download a JSON key for this service account
5. Store the key securely in Secret Manager as `gcp-service-account`

## Setting Up API Keys

Store your API keys in Secret Manager:

```bash
# For Portkey
gcloud secrets create portkey-api-key --replication-policy="automatic"
echo "YOUR_PORTKEY_API_KEY" | gcloud secrets versions add portkey-api-key --data-file=-

# For OpenRouter
gcloud secrets create openrouter --replication-policy="automatic"
echo "YOUR_OPENROUTER_API_KEY" | gcloud secrets versions add openrouter --data-file=-
```

## Manual Deployment

If you need to deploy manually:

1. Clone the repository

2. Navigate to the `infra` directory:
   ```bash
   cd infra
   ```

3. Initialize Terraform:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
   terraform init
   ```

4. Select workspace (environment):
   ```bash
   terraform workspace select dev  # or 'stage', 'prod'
   ```

5. Apply Terraform configuration:
   ```bash
   terraform apply -var="env=dev" -var="project_id=cherry-ai-project" -var="region=us-west4"
   ```

## CI/CD Pipeline

For automated deployments, the project uses Cloud Build:

1. Create a trigger in Cloud Build:
   - Name: `cherry-deploy-trigger`
   - Event: Push to branch
   - Source: Your repository
   - Configuration: Repository (`/infra/cloudbuild.yaml`)

2. Configure branch-to-environment mapping:
   - `main` → prod
   - `staging` → stage
   - All others → dev

## Configuring Custom Domain (Optional)

To use a custom domain:

1. Add a domain mapping in Cloud Run
2. Set up DNS records to point to the Cloud Run service
3. Configure SSL certificates

## Monitoring and Operations

The deployment includes:

- **Dashboards**: Find dashboard links in deployment outputs
- **Alerting**: Email notifications for critical events
- **Logging**: Structured logs in Cloud Logging
- **SLOs**: Service level objectives for availability and latency

## Troubleshooting

Common issues:

1. **Health check failures**:
   - Verify the service is running: `gcloud run services describe orchestrator-api-dev`
   - Check logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-api-dev"`

2. **Secret access issues**:
   - Verify the Cloud Run service account has Secret Accessor role
   - Check secret versions exist: `gcloud secrets versions list openrouter-dev`

3. **Network connectivity issues**:
   - Verify VPC connector is correctly configured
   - Check firewall rules allow necessary traffic

## Security Best Practices

The deployment implements:
- Default-deny firewall rules
- Least-privilege service accounts
- Secret Manager for credential storage
- VPC for network isolation
- Private Google Access for services
- Cloud Armor for edge protection (optional)

## Scaling Considerations

- Cloud Run scales automatically based on traffic
- Configure min/max instances based on your needs
- Redis cache size may need adjustment for heavy loads
- Monitor Firestore usage for appropriate scaling

## Cost Optimization

- Cloud Run only charges for actual usage
- Use minimum instances=0 in dev/staging for cost saving
- Enable Firestore TTL for older data
- Set up budget alerts in GCP Billing

## Reference

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Build CI/CD](https://cloud.google.com/build/docs/configuring-builds/create-basic-configuration)
