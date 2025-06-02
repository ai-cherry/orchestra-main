# Data Ingestion System - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the data ingestion system on Vultr using Pulumi infrastructure as code.

## Prerequisites

1. **Vultr Account**
   - Active Vultr account with API access
   - API key configured in environment

2. **Pulumi Setup**
   ```bash
   # Install Pulumi
   curl -fsSL https://get.pulumi.com | sh
   
   # Login to Pulumi backend
   pulumi login
   
   # Install required plugins
   pulumi plugin install resource vultr
   pulumi plugin install resource kubernetes
   ```

3. **Required Tools**
   - Python 3.9+
   - PostgreSQL client
   - kubectl
   - Docker

4. **Environment Variables**
   ```bash
   export VULTR_API_KEY="your-vultr-api-key"
   export PULUMI_CONFIG_PASSPHRASE="your-passphrase"
   export OPENAI_API_KEY="your-openai-key"  # For vector embeddings
   ```

## Deployment Steps

### 1. Infrastructure Deployment

#### Stage 1: Core Infrastructure

```bash
# Navigate to infrastructure directory
cd infrastructure/data_ingestion

# Create new Pulumi stack for staging
pulumi stack init staging

# Set configuration
pulumi config set region ewr
pulumi config set environment staging

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up --yes
```

#### Stage 2: Database Setup

```bash
# Get database credentials
export POSTGRES_HOST=$(pulumi stack output postgres_host)
export POSTGRES_PASSWORD=$(pulumi stack output postgres_connection_string --show-secrets | grep -oP 'postgresql://[^:]+:\K[^@]+')

# Apply database schema
psql -h $POSTGRES_HOST -U postgres -d data_ingestion < migrations/002_data_ingestion_schema.sql

# Verify schema
psql -h $POSTGRES_HOST -U postgres -d data_ingestion -c "\dt data_ingestion.*"
```

#### Stage 3: Kubernetes Services

```bash
# Get kubeconfig
pulumi stack output k8s_kubeconfig --show-secrets > ~/.kube/config-data-ingestion

# Set context
export KUBECONFIG=~/.kube/config-data-ingestion

# Verify cluster
kubectl get nodes

# Deploy application services
kubectl apply -f deploy/data-ingestion-services.yaml
```

### 2. Application Deployment

#### Build and Push Docker Images

```bash
# Build data ingestion service
docker build -t data-ingestion-api:latest -f Dockerfile.data-ingestion .

# Tag for registry
docker tag data-ingestion-api:latest registry.vultr.com/data-ingestion/api:latest

# Push to registry
docker push registry.vultr.com/data-ingestion/api:latest
```

#### Deploy Services

```yaml
# deploy/data-ingestion-services.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-ingestion-api
  namespace: data-ingestion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-ingestion-api
  template:
    metadata:
      labels:
        app: data-ingestion-api
    spec:
      containers:
      - name: api
        image: registry.vultr.com/data-ingestion/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: data-ingestion-secrets
              key: postgres-url
        - name: WEAVIATE_URL
          value: "http://weaviate:8080"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: data-ingestion-secrets
              key: redis-url
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: data-ingestion-api
  namespace: data-ingestion
spec:
  selector:
    app: data-ingestion-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### 3. Blue-Green Deployment

#### Deploy Green Environment

```bash
# Create green stack
pulumi stack init production-green

# Copy configuration from staging
pulumi config cp --stack staging

# Deploy green environment
pulumi up --yes

# Run smoke tests
./scripts/run_smoke_tests.sh green
```

#### Switch Traffic

```bash
# Update load balancer to point to green
pulumi config set active_environment green
pulumi up --yes

# Monitor metrics
./scripts/monitor_deployment.sh
```

#### Rollback Procedure

```bash
# If issues detected, switch back to blue
pulumi config set active_environment blue
pulumi up --yes

# Investigate issues in green
kubectl logs -n data-ingestion -l app=data-ingestion-api --tail=100
```

### 4. Post-Deployment Verification

#### Health Checks

```bash
# API health check
curl -f https://api.data-ingestion.example.com/health

# Database connectivity
psql -h $POSTGRES_HOST -U postgres -d data_ingestion -c "SELECT COUNT(*) FROM data_ingestion.file_imports;"

# Weaviate status
curl http://weaviate.data-ingestion.example.com/v1/.well-known/ready
```

#### Performance Tests

```bash
# Run performance test suite
python tests/performance/test_ingestion_throughput.py

# Check query response times
python tests/performance/test_query_latency.py
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# monitoring/prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'data-ingestion-api'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - data-ingestion
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: data-ingestion-api
```

### 2. Grafana Dashboards

Import the following dashboards:
- `dashboards/data-ingestion-overview.json`
- `dashboards/query-performance.json`
- `dashboards/storage-utilization.json`

### 3. Alerts Configuration

```yaml
# monitoring/alerts.yaml
groups:
- name: data_ingestion
  rules:
  - alert: HighQueryLatency
    expr: histogram_quantile(0.95, query_duration_seconds_bucket) > 0.1
    for: 5m
    annotations:
      summary: "Query latency exceeds 100ms"
      
  - alert: ProcessingQueueBacklog
    expr: processing_queue_depth > 1000
    for: 10m
    annotations:
      summary: "Processing queue depth exceeds threshold"
      
  - alert: StorageUtilizationHigh
    expr: storage_usage_percent > 80
    for: 15m
    annotations:
      summary: "Storage utilization above 80%"
```

## Secrets Management

### 1. Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace data-ingestion

# Create secrets
kubectl create secret generic data-ingestion-secrets \
  --namespace=data-ingestion \
  --from-literal=postgres-url="$POSTGRES_CONNECTION_STRING" \
  --from-literal=redis-url="$REDIS_CONNECTION_STRING" \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  --from-literal=s3-access-key="$S3_ACCESS_KEY" \
  --from-literal=s3-secret-key="$S3_SECRET_KEY"
```

### 2. Rotate Secrets

```bash
# Update secret
kubectl create secret generic data-ingestion-secrets \
  --namespace=data-ingestion \
  --from-literal=postgres-url="$NEW_POSTGRES_URL" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secrets
kubectl rollout restart deployment/data-ingestion-api -n data-ingestion
```

## Disaster Recovery

### 1. Backup Procedures

```bash
# Database backup
pg_dump -h $POSTGRES_HOST -U postgres -d data_ingestion \
  --schema=data_ingestion \
  --file=backup-$(date +%Y%m%d-%H%M%S).sql

# Weaviate backup
curl -X POST http://weaviate:8080/v1/backups \
  -H "Content-Type: application/json" \
  -d '{"id": "backup-'$(date +%Y%m%d-%H%M%S)'"}'

# S3 sync
aws s3 sync s3://data-ingestion-files s3://data-ingestion-backup --delete
```

### 2. Restore Procedures

```bash
# Restore database
psql -h $POSTGRES_HOST -U postgres -d data_ingestion < backup-20240102-120000.sql

# Restore Weaviate
curl -X POST http://weaviate:8080/v1/backups/backup-20240102-120000/restore

# Restore S3
aws s3 sync s3://data-ingestion-backup s3://data-ingestion-files --delete
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check pod memory
   kubectl top pods -n data-ingestion
   
   # Increase limits if needed
   kubectl edit deployment data-ingestion-api -n data-ingestion
   ```

2. **Slow Queries**
   ```sql
   -- Check query performance
   SELECT query, mean_exec_time, calls 
   FROM pg_stat_statements 
   WHERE query LIKE '%data_ingestion%' 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;
   
   -- Run EXPLAIN ANALYZE
   EXPLAIN ANALYZE SELECT * FROM data_ingestion.parsed_content WHERE ...;
   ```

3. **Processing Queue Stuck**
   ```bash
   # Check queue status
   kubectl exec -it deployment/data-ingestion-api -n data-ingestion -- \
     python -c "from app import check_queue_status; check_queue_status()"
   
   # Reset stuck items
   psql -h $POSTGRES_HOST -U postgres -d data_ingestion -c \
     "UPDATE data_ingestion.processing_queue SET locked_at = NULL WHERE locked_at < NOW() - INTERVAL '1 hour';"
   ```

### Debug Commands

```bash
# Get pod logs
kubectl logs -n data-ingestion -l app=data-ingestion-api --tail=100 -f

# Execute into pod
kubectl exec -it deployment/data-ingestion-api -n data-ingestion -- /bin/bash

# Check database connections
psql -h $POSTGRES_HOST -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'data_ingestion';"

# Weaviate health
curl -s http://weaviate:8080/v1/nodes | jq .
```

## Maintenance Windows

### Scheduled Maintenance

1. **Weekly Tasks**
   - Clean expired cache entries
   - Vacuum PostgreSQL tables
   - Update vector indices

2. **Monthly Tasks**
   - Rotate logs
   - Update dependencies
   - Performance review

### Maintenance Scripts

```bash
# maintenance/weekly.sh
#!/bin/bash
set -e

echo "Starting weekly maintenance..."

# Clean cache
psql -h $POSTGRES_HOST -U postgres -d data_ingestion -c \
  "SELECT data_ingestion.clean_expired_cache();"

# Vacuum tables
psql -h $POSTGRES_HOST -U postgres -d data_ingestion -c \
  "VACUUM ANALYZE data_ingestion.parsed_content;"

# Refresh materialized views
psql -h $POSTGRES_HOST -U postgres -d data_ingestion -c \
  "REFRESH MATERIALIZED VIEW data_ingestion.source_statistics;"

echo "Weekly maintenance completed"
```

## Security Checklist

- [ ] All secrets stored in Kubernetes secrets
- [ ] Network policies configured
- [ ] RBAC policies applied
- [ ] TLS enabled on all endpoints
- [ ] Regular security scans scheduled
- [ ] Audit logging enabled
- [ ] Backup encryption configured
- [ ] Access logs monitored

## Contact Information

- **On-Call**: data-ingestion-oncall@example.com
- **Escalation**: platform-team@example.com
- **Runbook**: https://wiki.example.com/data-ingestion-runbook