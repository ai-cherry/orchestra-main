# Orchestra AI Operations Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [CLI Operations](#cli-operations)
4. [Deployment](#deployment)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Troubleshooting](#troubleshooting)
7. [Security](#security)
8. [Architecture](#architecture)

---

## System Overview

Orchestra AI is a cloud-native, AI-powered orchestration platform built on Google Cloud Platform (GCP). It features:

- **MCP (Model Context Protocol)** servers for modular AI capabilities
- **Web scraping AI agent teams** with Zenrows, Apify, and PhantomBuster
- **Enhanced vector memory system** with Redis caching
- **Multi-source data integration** (Gong, Salesforce, HubSpot, Slack, Looker)
- **GCP-native integration** with Pub/Sub, Service Directory, and Cloud Monitoring

### Key Services

| Service                | Purpose           | URL Pattern                              |
| ---------------------- | ----------------- | ---------------------------------------- |
| `ai-orchestra-minimal` | Main orchestrator | `https://ai-orchestra-minimal-*.run.app` |
| `web-scraping-agents`  | Web scraping team | `https://web-scraping-agents-*.run.app`  |
| `admin-interface`      | Admin UI          | `https://admin-interface-*.run.app`      |

---

## Quick Start

### Prerequisites

- Python 3.10+
- `gcloud` CLI configured
- Access to GCP project `cherry-ai-project`
- Required API keys in GCP Secret Manager

### Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd orchestra-main

# Set up Python environment
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Initialize system
python tools/orchestra_cli.py init
```

This will:

1. Sync all secrets from GCP Secret Manager
2. Validate configuration
3. Run comprehensive health checks

---

## CLI Operations

The Orchestra CLI (`tools/orchestra_cli.py`) is your primary interface for system management.

### Secrets Management

#### Sync Secrets from GCP

```bash
# Sync all secrets to local .env
python tools/orchestra_cli.py secrets sync

# Dry run to see what would be synced
python tools/orchestra_cli.py secrets sync --dry-run

# Sync to custom env file
python tools/orchestra_cli.py secrets sync --env-file .env.local
```

#### Validate Secrets

```bash
# Check all required secrets are present
python tools/orchestra_cli.py secrets validate
```

#### Set/Update Secrets in GCP

```bash
# Set a new secret (will prompt for value)
python tools/orchestra_cli.py secrets set MY_API_KEY

# Update existing secret
python tools/orchestra_cli.py secrets set OPENAI_API_KEY
```

### Adapter Management

#### List Adapters

```bash
# Show all adapters and their status
python tools/orchestra_cli.py adapters list
```

Output:

```
┌─────────────┬─────────────┬──────────────────────┬─────────────────────────────┬─────────────────┐
│ Adapter     │ Name        │ Description          │ Required Secrets            │ Status          │
├─────────────┼─────────────┼──────────────────────┼─────────────────────────────┼─────────────────┤
│ gong        │ Gong.io     │ Call recordings      │ GONG_API_KEY                │ ✓ Ready         │
│ salesforce  │ Salesforce  │ CRM data            │ SALESFORCE_CLIENT_ID, ...   │ ✗ Missing secrets│
└─────────────┴─────────────┴──────────────────────┴─────────────────────────────┴─────────────────┘
```

#### Check Adapter Configuration

```bash
# Validate specific adapter
python tools/orchestra_cli.py adapters check salesforce
```

### System Diagnostics

#### Health Check

```bash
# Run comprehensive health checks
python tools/orchestra_cli.py diagnostics health
```

This checks:

- Secret availability
- GCP connectivity
- Redis connection
- MCP Gateway status
- Adapter readiness

### Orchestrator Management

#### Reload Configuration

```bash
# Reload after config changes
python tools/orchestra_cli.py orchestrator reload
```

#### Check Status

```bash
# Show orchestrator status
python tools/orchestra_cli.py orchestrator status
```

---

## Deployment

### CI/CD Pipeline

Deployment is automated via GitHub Actions when pushing to `main` branch:

1. **Secret Validation**: Ensures all required secrets exist in GCP
2. **Testing & Linting**: Runs pytest and code quality checks
3. **Cloud Build**: Builds and pushes Docker images
4. **Deployment**: Updates Cloud Run services
5. **Health Checks**: Validates services are healthy

### Manual Deployment

```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=COMMIT_SHA=$(git rev-parse HEAD)

# Deploy specific service
gcloud run deploy ai-orchestra-minimal \
  --image us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images/orchestra-main:latest \
  --region us-central1
```

### Pulumi Infrastructure

```bash
# Navigate to infrastructure directory
cd infra/pulumi_gcp

# Preview changes
pulumi preview

# Apply changes
pulumi up

# View outputs
pulumi stack output
```

Key infrastructure components:

- **VPC & Subnets**: Isolated network for services
- **Service Accounts**: Least-privilege IAM per service
- **Pub/Sub Topics**: Event-driven communication
- **Service Directory**: Dynamic service discovery
- **Cloud Monitoring**: Dashboards and alerts

---

## Monitoring & Alerting

### Dashboard

Access the Orchestra AI dashboard:

```
https://console.cloud.google.com/monitoring/dashboards/custom/[dashboard-id]?project=cherry-ai-project
```

Metrics tracked:

- Request rate per service
- Error rates
- Memory usage
- Response latencies

### Uptime Checks

Automated health checks run every 60 seconds for:

- Orchestra API (`/health`)
- Web Scraping Service (`/health`)
- Admin Interface (`/`)

### Alert Policies

| Alert             | Condition          | Threshold     |
| ----------------- | ------------------ | ------------- |
| High Error Rate   | Error rate > 5%    | 5 minutes     |
| High Memory Usage | Memory > 90%       | 5 minutes     |
| Service Down      | Uptime check fails | 2 consecutive |

### Log-Based Metrics

Custom metrics track:

- MCP server errors by type
- Tool call success/failure rates
- Agent performance metrics

### Viewing Logs

```bash
# Stream logs for a service
gcloud run services logs read ai-orchestra-minimal \
  --region us-central1 \
  --tail 50 \
  --follow

# Query specific errors
gcloud logging read 'resource.type="cloud_run_revision" AND severity="ERROR"' \
  --limit 50 \
  --format json
```

---

## Troubleshooting

### Common Issues

#### 1. Service Unhealthy

**Symptoms**: Health check returns 503, service not responding

**Resolution**:

```bash
# Check service logs
gcloud run services logs read [service-name] --region us-central1 --limit 100

# Check secret availability
python tools/orchestra_cli.py secrets validate

# Force service restart
gcloud run services update [service-name] --region us-central1 --no-traffic
gcloud run services update [service-name] --region us-central1 --to-latest
```

#### 2. Missing Secrets

**Symptoms**: Services fail to start, "Missing required secrets" error

**Resolution**:

```bash
# List what's missing
python tools/orchestra_cli.py secrets validate

# Set missing secrets
python tools/orchestra_cli.py secrets set MISSING_SECRET_NAME

# Sync to local environment
python tools/orchestra_cli.py secrets sync
```

#### 3. Redis Connection Failed

**Symptoms**: "Connection failed: Connection refused" in health checks

**Resolution**:

```bash
# Check Redis instance status
gcloud redis instances describe orchestra-redis --region us-central1

# Get Redis host
gcloud redis instances describe orchestra-redis \
  --region us-central1 \
  --format "value(host)"

# Update secret if needed
python tools/orchestra_cli.py secrets set REDIS_HOST
```

#### 4. High Memory Usage

**Symptoms**: Alert triggered, service performance degraded

**Resolution**:

```bash
# Check current usage
gcloud monitoring read \
  'resource.type="cloud_run_revision" AND
   resource.labels.service_name="[service-name]" AND
   metric.type="run.googleapis.com/container/memory/utilizations"' \
  --start-time -1h

# Scale up if needed
gcloud run services update [service-name] \
  --memory 8Gi \
  --region us-central1
```

### Debug Commands

```bash
# Get service details
gcloud run services describe [service-name] --region us-central1

# List recent revisions
gcloud run revisions list --service [service-name] --region us-central1

# Check IAM bindings
gcloud run services get-iam-policy [service-name] --region us-central1

# Test service directly
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://[service-url]/health
```

---

## Security

### Service Accounts

Each service runs with least-privilege IAM:

| Service      | Service Account             | Key Permissions                     |
| ------------ | --------------------------- | ----------------------------------- |
| Orchestrator | `orchestra-orchestrator-sa` | Pub/Sub, Service Directory, Secrets |
| Web Scraping | `orchestra-webscraping-sa`  | Redis, Pub/Sub, Secrets             |
| Admin        | `orchestra-admin-sa`        | Read-only monitoring, logs          |

### Secret Rotation

```bash
# Rotate a secret
python tools/orchestra_cli.py secrets set API_KEY_NAME

# Redeploy services to pick up new secret
gcloud run services update [service-name] --region us-central1 --to-latest
```

### Network Security

- All services run in isolated VPC
- Redis accessible only within VPC
- HTTPS enforced on all endpoints
- No public IPs on compute resources

---

## Architecture

### Service Communication

```
┌─────────────────┐     ┌─────────────────┐
│   Orchestrator  │────▶│    Pub/Sub      │
└─────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│Service Directory│     │  Web Scraping   │
└─────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│     Redis       │◀────│   Monitoring    │
└─────────────────┘     └─────────────────┘
```

### Event Flow

1. **Tool Call**: Client → Orchestrator → Pub/Sub
2. **Task Assignment**: Pub/Sub → Agent → Redis Queue
3. **Result Storage**: Agent → Redis → Vector Memory
4. **Health Check**: Monitoring → Service → Service Directory

### Scaling Strategy

- **Orchestrator**: 0-10 instances, CPU-based
- **Web Scraping**: 1-20 instances, queue-based
- **Admin**: 0-5 instances, request-based

---

## Best Practices

### Development

1. **Always validate secrets** before deployment
2. **Use the CLI** for all operations (avoid manual GCP console changes)
3. **Test locally** with synced secrets before pushing
4. **Monitor logs** during deployment for early issue detection

### Production

1. **Set up alerts** for your notification channels
2. **Review dashboards** weekly for trends
3. **Rotate secrets** quarterly or on compromise
4. **Scale proactively** based on monitoring data
5. **Document changes** in deployment commits

### Emergency Response

1. **Service Down**:

   - Check health endpoint
   - Review recent deployments
   - Roll back if needed
   - Check secrets and dependencies

2. **Data Loss**:

   - Redis has replication enabled
   - Firestore has automatic backups
   - Check audit logs for actions

3. **Security Incident**:
   - Rotate all affected secrets immediately
   - Review IAM audit logs
   - Update service accounts if compromised
   - Enable additional monitoring

---

## Appendix

### Environment Variables

Required environment variables for local development:

```bash
# Core
GOOGLE_CLOUD_PROJECT=cherry-ai-project
ENVIRONMENT=development

# APIs
OPENAI_API_KEY=sk-...
PORTKEY_API_KEY=...

# Infrastructure
REDIS_HOST=...
REDIS_PASSWORD=...

# Web Scraping
ZENROWS_API_KEY=...
APIFY_API_KEY=...
```

### Useful Links

- [GCP Console](https://console.cloud.google.com/?project=cherry-ai-project)
- [Cloud Run Services](https://console.cloud.google.com/run?project=cherry-ai-project)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager?project=cherry-ai-project)
- [Monitoring Dashboard](https://console.cloud.google.com/monitoring?project=cherry-ai-project)
- [Cloud Build History](https://console.cloud.google.com/cloud-build/builds?project=cherry-ai-project)

### Support

For issues or questions:

1. Check this guide's troubleshooting section
2. Review service logs in Cloud Logging
3. Check monitoring dashboards for anomalies
4. Verify all secrets are properly configured
