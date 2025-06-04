# Cherry AI Operations Guide

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

Cherry AI is a cloud-native, AI-powered coordination platform built on
- **MCP (Model Context Protocol)** servers for modular AI capabilities
- **Web scraping AI agent teams** with Zenrows, Apify, and PhantomBuster
- **Enhanced vector memory system** with Redis caching
- **Multi-source data integration** (Gong, Salesforce, HubSpot, Slack, Looker)
- **
### Key Services

| Service                | Purpose           | URL Pattern                              |
| ---------------------- | ----------------- | ---------------------------------------- |
| `ai-cherry_ai-minimal` | Main conductor | `https://ai-cherry_ai-minimal-*.run.app` |
| `web-scraping-agents`  | Web scraping team | `https://web-scraping-agents-*.run.app`  |
| `admin-interface`      | Admin UI          | `https://admin-interface-*.run.app`      |

---

## Quick Start

### Prerequisites

- Python 3.10+
- `gcloud` CLI configured
- Access to - Required API keys in
### Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd cherry_ai-main

# Set up Python environment
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Initialize system
python tools/cherry_ai_cli.py init
```

This will:

1. Sync all secrets from 2. Validate configuration
3. Run comprehensive health checks

---

## CLI Operations

The cherry_ai CLI (`tools/cherry_ai_cli.py`) is your primary interface for system management.

### Secrets Management

#### Sync Secrets from
```bash
# Sync all secrets to local .env
python tools/cherry_ai_cli.py secrets sync

# Dry run to see what would be synced
python tools/cherry_ai_cli.py secrets sync --dry-run

# Sync to custom env file
python tools/cherry_ai_cli.py secrets sync --env-file .env.local
```

#### Validate Secrets

```bash
# Check all required secrets are present
python tools/cherry_ai_cli.py secrets validate
```

#### Set/Update Secrets in
```bash
# Set a new secret (will prompt for value)
python tools/cherry_ai_cli.py secrets set MY_API_KEY

# Update existing secret
python tools/cherry_ai_cli.py secrets set OPENAI_API_KEY
```

### Adapter Management

#### List Adapters

```bash
# Show all adapters and their status
python tools/cherry_ai_cli.py adapters list
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
python tools/cherry_ai_cli.py adapters check salesforce
```

### System Diagnostics

#### Health Check

```bash
# Run comprehensive health checks
python tools/cherry_ai_cli.py diagnostics health
```

This checks:

- Secret availability
- - Redis connection
- MCP Gateway status
- Adapter readiness

### conductor Management

#### Reload Configuration

```bash
# Reload after config changes
python tools/cherry_ai_cli.py conductor reload
```

#### Check Status

```bash
# Show conductor status
python tools/cherry_ai_cli.py conductor status
```

---

## Deployment

### CI/CD Pipeline

Deployment is automated via GitHub Actions when pushing to `main` branch:

1. **Secret Validation**: Ensures all required secrets exist in 2. **Testing & Linting**: Runs pytest and code quality checks
3. **Cloud Build**: Builds and pushes Docker images
4. **Deployment**: Updates 5. **Health Checks**: Validates services are healthy

### Manual Deployment

```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=COMMIT_SHA=$(git rev-parse HEAD)

# Deploy specific service
g  --image us-central1-docker.pkg.dev/cherry-ai-project/cherry_ai-images/cherry_ai-main:latest \
  --region us-central1
```

### Pulumi Infrastructure

```bash
# Navigate to infrastructure directory
cd infra/pulumi_
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

Access the Cherry AI dashboard:

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

- cherry_ai API (`/health`)
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
g  --region us-central1 \
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
g
# Check secret availability
python tools/cherry_ai_cli.py secrets validate

# Force service restart
gg```

#### 2. Missing Secrets

**Symptoms**: Services fail to start, "Missing required secrets" error

**Resolution**:

```bash
# List what's missing
python tools/cherry_ai_cli.py secrets validate

# Set missing secrets
python tools/cherry_ai_cli.py secrets set MISSING_SECRET_NAME

# Sync to local environment
python tools/cherry_ai_cli.py secrets sync
```

#### 3. Redis Connection Failed

**Symptoms**: "Connection failed: Connection refused" in health checks

**Resolution**:

```bash
# Check Redis instance status
gcloud redis instances describe cherry_ai-redis --region us-central1

# Get Redis host
gcloud redis instances describe cherry_ai-redis \
  --region us-central1 \
  --format "value(host)"

# Update secret if needed
python tools/cherry_ai_cli.py secrets set REDIS_HOST
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
g  --memory 8Gi \
  --region us-central1
```

### Debug Commands

```bash
# Get service details
g
# List recent revisions
g
# Check IAM bindings
g
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
| conductor | `cherry_ai-conductor-sa` | Pub/Sub, Service Directory, Secrets |
| Web Scraping | `cherry_ai-webscraping-sa`  | Redis, Pub/Sub, Secrets             |
| Admin        | `cherry_ai-admin-sa`        | Read-only monitoring, logs          |

### Secret Rotation

```bash
# Rotate a secret
python tools/cherry_ai_cli.py secrets set API_KEY_NAME

# Redeploy services to pick up new secret
g```

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
│   conductor  │────▶│    Pub/Sub      │
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

1. **Tool Call**: Client → conductor → Pub/Sub
2. **Task Assignment**: Pub/Sub → Agent → Redis Queue
3. **Result Storage**: Agent → Redis → Vector Memory
4. **Health Check**: Monitoring → Service → Service Directory

### Scaling Strategy

- **conductor**: 0-10 instances, CPU-based
- **Web Scraping**: 1-20 instances, queue-based
- **Admin**: 0-5 instances, request-based

---

## Best Practices

### Development

1. **Always validate secrets** before deployment
2. **Use the CLI** for all operations (avoid manual 3. **Test locally** with synced secrets before pushing
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
   - MongoDB
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

- [- [- [- [Monitoring Dashboard](https://console.cloud.google.com/monitoring?project=cherry-ai-project)
- [Cloud Build History](https://console.cloud.google.com/cloud-build/builds?project=cherry-ai-project)

### Support

For issues or questions:

1. Check this guide's troubleshooting section
2. Review service logs in Cloud Logging
3. Check monitoring dashboards for anomalies
4. Verify all secrets are properly configured
