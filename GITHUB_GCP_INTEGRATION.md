# GitHub and GCP Integration for AI Orchestra

This document outlines the implementation of the GitHub and GCP integration optimization plan for the AI Orchestra project. The implementation focuses on stability, performance, and resource optimization for this one-person project.

## 1. Implementation Overview

The implementation includes several components:

1. **GitHub Token Management**

   - Token rotation script
   - Token usage monitoring
   - Secret synchronization between GitHub and GCP

2. **GCP Service Account Management**

   - Service account key rotation
   - Least privilege implementation

3. **CI/CD Pipeline Optimization**

   - Dependency caching
   - Parallel job execution
   - Performance testing

4. **Resource Optimization**
   - Firestore client pooling and result caching
   - Vertex AI cost management
   - Cloud Run configuration optimization

## 2. Implemented Components

### 2.1. GitHub Token Management

#### 2.1.1. Token Rotation Script (`scripts/rotate_github_tokens.sh`)

This script automates the rotation of GitHub tokens and updates them in both GitHub Actions secrets and GCP Secret Manager. Features include:

- Secure token rotation with minimal manual intervention
- Synchronization between GitHub and GCP Secret Manager
- Automatic cleanup of old tokens

#### 2.1.2. Token Usage Monitoring (`scripts/monitor_token_usage.sh`)

This script monitors GitHub token usage to prevent rate limiting issues. Features include:

- Real-time monitoring of token rate limits
- Configurable alert thresholds
- Integration with notification systems (Slack)
- Recommendations for avoiding rate limiting

### 2.2. GCP Service Account Management

#### 2.2.1. Service Account Key Rotation (`scripts/rotate_service_account_keys.sh`)

This script automates the rotation of GCP service account keys and updates them in both GitHub Actions secrets and GCP Secret Manager. Features include:

- Secure key rotation with minimal manual intervention
- Synchronization between GitHub and GCP Secret Manager
- Automatic cleanup of old keys to maintain security

#### 2.2.2. Secret Synchronization (`scripts/sync_github_gcp_secrets.sh`)

This script ensures credentials are consistent across both GitHub and GCP Secret Manager. Features include:

- Bidirectional synchronization
- Support for multiple secrets
- Secure handling of sensitive information

### 2.3. CI/CD Pipeline Optimization

#### 2.3.1. Optimized GitHub Actions Workflow (`.github/workflows/optimized-build-deploy.yml`)

This workflow template includes several optimizations:

- Dependency caching for faster builds
- Parallel job execution for tests
- Performance testing with benchmarking
- Workload Identity Federation authentication
- Automated deployment to Cloud Run
- Deployment verification and monitoring

### 2.4. Resource Optimization

#### 2.4.1. Firestore Optimization (`ai-orchestra/infrastructure/persistence/firestore_optimized.py`)

This implementation provides performance-optimized Firestore operations:

- Connection pooling to reduce connection overhead
- Result caching to minimize redundant queries
- Batch operations for efficient writes
- Async/await patterns for better concurrency

#### 2.4.2. Vertex AI Cost Management (`ai-orchestra/infrastructure/gcp/vertex_ai_cost_manager.py`)

This component helps monitor and control costs for Vertex AI usage:

- Budget tracking and alerts
- Usage monitoring for specific models
- Cost optimization recommendations
- Quota management to prevent overages
- Integration with Secret Manager for secure budget configuration

## 3. Usage Instructions

### 3.1. GitHub Token Management

To rotate GitHub tokens:

```bash
./scripts/rotate_github_tokens.sh
```

To monitor token usage:

```bash
./scripts/monitor_token_usage.sh
```

To install the monitoring as a cron job:

```bash
./scripts/monitor_token_usage.sh --install-cron
```

### 3.2. GCP Service Account Management

To rotate service account keys:

```bash
./scripts/rotate_service_account_keys.sh
```

To synchronize secrets between GitHub and GCP:

```bash
# Bidirectional sync (default)
./scripts/sync_github_gcp_secrets.sh

# From GitHub to GCP
./scripts/sync_github_gcp_secrets.sh github-to-gcp

# From GCP to GitHub
./scripts/sync_github_gcp_secrets.sh gcp-to-github
```

### 3.3. CI/CD Pipeline

The optimized GitHub Actions workflow is automatically triggered on:

- Pushes to the main branch
- Manual workflow dispatch

You can manually trigger the workflow from the GitHub Actions tab in your repository.

### 3.4. Resource Optimization

To use the optimized Firestore implementation:

```python
from ai_orchestra.infrastructure.persistence.firestore_optimized import OptimizedFirestoreMemoryProvider

# Initialize the provider
memory_provider = OptimizedFirestoreMemoryProvider(
    collection_name="memory",
    cache_ttl=300,  # 5 minutes
    cache_size=1000
)

# Use the provider
await memory_provider.store("key", "value")
value = await memory_provider.retrieve("key")
```

To use the Vertex AI cost manager:

```python
from ai_orchestra.infrastructure.gcp.vertex_ai_cost_manager import VertexAICostManager

# Initialize the manager
cost_manager = VertexAICostManager(
    project_id="cherry-ai-project",
    budget_limit=100.0,
    alert_threshold=0.8
)

# Check if within budget
if await cost_manager.is_within_budget():
    # Proceed with operation
    pass
else:
    # Take cost-saving measures
    pass

# Get cost optimization recommendations
recommendations = await cost_manager.get_cost_optimization_recommendations()
for rec in recommendations:
    print(f"{rec['severity']}: {rec['message']}")
    for action in rec['actions']:
        print(f"  - {action}")
```

## 4. Next Steps

1. **Testing**: Thoroughly test all components in a development environment before deploying to production.
2. **Documentation**: Update project documentation to reflect the new components and workflows.
3. **Monitoring**: Set up monitoring for the new components to ensure they are functioning correctly.
4. **Training**: Provide training for team members on the new workflows and tools.
5. **Continuous Improvement**: Regularly review and improve the implementation based on feedback and changing requirements.

## 5. Conclusion

This implementation provides a comprehensive approach to optimizing GitHub and GCP integration for the AI Orchestra project. By focusing on stability, performance, and resource optimization, it helps streamline workflows, enhance CI/CD pipelines, automate deployments, and improve overall system reliability.
