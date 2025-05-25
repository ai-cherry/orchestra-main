# Automation System Execution Architecture

This document details the execution mechanisms for all automation systems in the AI Orchestra project, explaining how each component is triggered, when it runs, and where it executes.

## Trigger Mechanisms Overview

The AI Orchestra automation systems employ four distinct trigger mechanisms:

1. **Manual Invocation**: Direct execution by developers or operators
2. **Scheduled Execution**: Time-based triggering through various schedulers
3. **Event-based Execution**: Triggered by system events or thresholds
4. **Continuous Monitoring**: Long-running processes that self-regulate

## Execution Environments

The automation systems operate in several distinct environments:

| Environment            | Description                    | Best For                         |
| ---------------------- | ------------------------------ | -------------------------------- |
| Cloud Run Services     | Serverless container execution | Event-driven workloads           |
| Compute Engine VM      | Dedicated virtual machine      | Long-running monitoring          |
| GitHub Actions Runners | CI/CD pipeline execution       | Repository-triggered automations |
| GKE Pods               | Kubernetes-managed containers  | Scheduled jobs and services      |
| Local Development      | Developer workstation          | Testing and debugging            |

## System-Specific Execution Details

### 1. Performance Enhancement System

**Trigger Mechanisms:**

- **Primary**: Cloud Scheduler job triggering Cloud Run service
- **Secondary**: Metric-based alerts via Cloud Monitoring
- **Manual**: Direct invocation through automation controller

**Execution Timing:**

- Regular scheduled analysis (configurable, default: every 24 hours)
- On-demand when manually triggered
- Reactive execution when system metrics exceed defined thresholds:
  - CPU utilization > 70%
  - Memory utilization > 80%
  - P95 latency > 500ms
  - Error rate > 1%

**Execution Flow:**

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Cloud Scheduler    │─────►│  Cloud Run Service  │─────►│  Performance        │
│  (Time-based)       │      │  (Automation        │      │  Enhancement        │
│                     │      │   Controller)       │      │  Engine             │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
                                      ▲
┌─────────────────────┐              │              ┌─────────────────────┐
│                     │              │              │                     │
│  Cloud Monitoring   │──────────────┘              │  Manual CLI         │
│  Alert              │                             │  Invocation         │
│                     │                             │                     │
└─────────────────────┘                             └─────────────────────┘
```

**Environment Configuration:**

- Cloud Run service with appropriate IAM permissions
- Environment variables set from Secret Manager
- Memory allocation: 1Gi minimum for analysis operations
- CPU allocation: 1 CPU minimum, 2 CPU recommended
- Timeout: 15 minutes (sufficient for most analyses)

**Implementation in GitHub Actions:**

```yaml
name: Performance Enhancement

on:
  schedule:
    - cron: "0 2 * * *" # Run daily at 2 AM UTC
  workflow_dispatch: # Allow manual triggering

jobs:
  run-performance-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.SERVICE_ACCOUNT }}

      - id: performance-enhancement
        run: |
          python fully_automated_performance_enhancement.py \
            --environment ${{ github.ref == 'refs/heads/main' && 'production' || 'development' }} \
            --automation-level 2 \
            --mode apply
```

### 2. Workspace Optimization Tool

**Trigger Mechanisms:**

- **Primary**: Git hook (pre-commit, post-merge)
- **Secondary**: Scheduled maintenance job
- **Manual**: Developer-initiated execution

**Execution Timing:**

- During local development (pre-commit hook)
- After merging changes (post-merge hook)
- Weekly scheduled maintenance
- When repository size exceeds configured thresholds
- On-demand developer optimization

**Execution Flow:**

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Git Hooks          │─────►│  Workspace          │─────►│  Optimization       │
│  (pre-commit)       │      │  Optimization       │      │  Actions            │
│                     │      │  Tool               │      │                     │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
                                      ▲
┌─────────────────────┐              │              ┌─────────────────────┐
│                     │              │              │                     │
│  Weekly GitHub      │──────────────┘              │  IDE Extension      │
│  Action             │                             │  Button             │
│                     │                             │                     │
└─────────────────────┘                             └─────────────────────┘
```

**Environment Configuration:**

- Local developer environment with Git hooks installed
- GitHub Actions runner for scheduled maintenance
- VSCode extension for IDE integration

**Implementation in Git Hooks:**

Pre-commit configuration (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: local
    hooks:
      - id: workspace-optimization
        name: Workspace Optimization
        entry: python workspace_optimization.py --analyze-only
        language: system
        pass_filenames: false
        always_run: true
```

### 3. Unified Automation Controller

**Trigger Mechanisms:**

- **Primary**: Cloud Scheduler for regularly scheduled execution
- **Secondary**: Pub/Sub messages for event-driven execution
- **Tertiary**: GitHub Actions for CI/CD-integrated execution
- **Manual**: Direct CLI invocation

**Execution Timing:**

- Continuous mode on dedicated VM or GKE deployment
- Scheduled intervals for various tasks:
  - Performance analysis: every 24 hours
  - Workspace optimization: weekly
  - Cost analysis: daily
  - Testing: various frequencies by test type
  - Infrastructure adaptation: daily

**Execution Flow:**

```
                                 ┌─────────────────────┐
                                 │                     │
                                 │  Automation         │
                                 │  Controller         │
                                 │                     │
                                 └─────────┬───────────┘
                                           │
                                           │
                                           ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│                 │  │                 │  │                 │  │                 │
│  Performance    │  │  Workspace      │  │  Deployment     │  │  Testing        │
│  Enhancement    │  │  Optimization   │  │  Pipeline       │  │  Automation     │
│                 │  │                 │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│                 │  │                 │  │                 │
│  AI Service     │  │  Cost           │  │  Infrastructure │
│  Optimization   │  │  Optimization   │  │  Adaptation     │
│                 │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Environment Configuration:**

- **Development**: Local execution with limited permissions
- **Staging**: Cloud Run service with moderate permissions
- **Production**: GKE deployment with appropriate security context

## Deployment Configurations for Production

### Cloud Run Service Deployment

```terraform
resource "google_cloud_run_service" "automation_controller" {
  name     = "automation-controller"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/automation-controller:latest"

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "CONFIG_PATH"
          value = "/etc/automation/config.yaml"
        }

        volume_mounts {
          name       = "config-volume"
          mount_path = "/etc/automation"
        }
      }

      volumes {
        name = "config-volume"
        secret {
          secret_name = "automation-config"
          items {
            key  = "config.yaml"
            path = "config.yaml"
          }
        }
      }

      service_account_name = google_service_account.automation_service_account.email
    }
  }
}
```

### GKE Deployment for Continuous Mode

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: automation-controller
  namespace: ai-orchestra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: automation-controller
  template:
    metadata:
      labels:
        app: automation-controller
    spec:
      containers:
        - name: automation-controller
          image: gcr.io/PROJECT_ID/automation-controller:latest
          args:
            - "--mode"
            - "continuous"
            - "--environment"
            - "production"
            - "--config"
            - "/etc/automation/config.yaml"
          resources:
            requests:
              cpu: "1"
              memory: "1Gi"
            limits:
              cpu: "2"
              memory: "2Gi"
          volumeMounts:
            - name: config-volume
              mountPath: /etc/automation
      volumes:
        - name: config-volume
          secret:
            secretName: automation-config
      serviceAccountName: automation-service-account
```

### Cloud Scheduler Configuration

```terraform
resource "google_cloud_scheduler_job" "daily_performance_enhancement" {
  name        = "daily-performance-enhancement"
  description = "Trigger daily performance enhancement analysis"
  schedule    = "0 2 * * *"  # 2 AM daily
  time_zone   = "UTC"

  http_target {
    uri         = "${google_cloud_run_service.automation_controller.status[0].url}/tasks/performance"
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.scheduler_service_account.email
    }

    body = base64encode(jsonencode({
      "mode": "apply",
      "environment": var.environment
    }))
  }
}
```

## Environmental Triggers and Conditions

### Performance Enhancement Triggers

| Trigger Type  | Condition                        | Action                         | Environment |
| ------------- | -------------------------------- | ------------------------------ | ----------- |
| Scheduled     | Daily at 2 AM                    | Full analysis and optimization | All         |
| CPU Alert     | Utilization > 70% for 15 minutes | Focused CPU optimization       | All         |
| Memory Alert  | Utilization > 80% for 10 minutes | Memory optimization            | All         |
| Latency Alert | P95 > 500ms for 5 minutes        | API and caching optimization   | Prod only   |
| Manual        | User request                     | User-specified optimization    | All         |

### Workspace Optimization Triggers

| Trigger Type    | Condition          | Action                      | Environment |
| --------------- | ------------------ | --------------------------- | ----------- |
| Git Hook        | Pre-commit         | Analyze workspace           | Local       |
| Git Hook        | Post-merge         | Optimize workspace          | Local       |
| Scheduled       | Weekly (Sunday)    | Full optimization           | All         |
| Repository Size | > 80% of threshold | Size optimization           | All         |
| Manual          | User request       | User-specified optimization | All         |

### Deployment Pipeline Triggers

| Trigger Type | Condition                | Action                          | Environment         |
| ------------ | ------------------------ | ------------------------------- | ------------------- |
| Git Push     | Branch = main            | Deploy to production            | Production          |
| Git Push     | Branch = develop         | Deploy to staging               | Staging             |
| Git Push     | Any feature branch       | Deploy to development           | Development         |
| Manual       | Approval received        | Deploy to specified environment | All                 |
| Scheduled    | Within deployment window | Apply pending deployments       | Staging, Production |

## Self-Healing Mechanisms

The automation systems include several self-healing mechanisms:

1. **Automatic Retries**: Failed operations automatically retry with exponential backoff
2. **Circuit Breakers**: Prevents cascading failures by breaking chains of dependent operations
3. **Health Checks**: Regular self-diagnostics with automatic recovery
4. **State Recovery**: Persistent state storage with recovery capabilities
5. **Rollback Capability**: Automatic rollback to last known good state on failure

## Conclusion

This automation execution architecture provides a robust, flexible framework for triggering and executing optimization, testing, deployment, and monitoring tasks across the AI Orchestra project. The combination of scheduled, event-driven, and continuous execution ensures comprehensive coverage while respecting environment-specific constraints and permissions.

The design prioritizes:

1. **Security**: Least-privilege service accounts and secure secret management
2. **Reliability**: Self-healing mechanisms and automatic recovery
3. **Scalability**: Cloud-native infrastructure that scales with workload
4. **Observability**: Comprehensive logging and monitoring
5. **Configurability**: YAML-based configuration for all aspects of execution

This architecture enables fully automated operation while maintaining appropriate gates and approvals for sensitive environments, striking the right balance between automation and control.
