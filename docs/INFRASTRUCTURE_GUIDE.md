# AI Orchestra Infrastructure Guide

## Overview

AI Orchestra is a multi-agent AI system deployed on Google Cloud Platform (GCP) using Kubernetes (GKE) for container orchestration and Pulumi for infrastructure as code. The system integrates SuperAGI for agent management with a sophisticated memory architecture.

## Architecture

### Core Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub Push   │────▶│ GitHub Actions  │────▶│  Pulumi Deploy  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GKE Cluster                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  SuperAGI   │  │ DragonflyDB │  │   MongoDB   │            │
│  │  (3 pods)   │  │ (Redis-like)│  │ (StatefulSet)│           │
│  └──────┬──────┘  └─────────────┘  └─────────────┘            │
│         │                                                       │
│  ┌──────▼──────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ MCP MongoDB │  │MCP Weaviate │  │  Firestore  │           │
│  │   Server    │  │   Server    │  │   (GCP)     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Language | Python | 3.10 | Primary development language |
| Infrastructure | Pulumi | 3.100+ | Infrastructure as Code |
| Container Runtime | Kubernetes (GKE) | Latest | Container orchestration |
| Package Management | pip/venv | - | Python dependencies |
| CI/CD | GitHub Actions | - | Automated deployment |
| Agent Framework | SuperAGI | Latest | AI agent management |
| Short-term Memory | DragonflyDB | Latest | Redis-compatible cache |
| Structured Storage | MongoDB | 7.0 | Document database |
| Vector Storage | Weaviate | Latest | Semantic search |
| Cloud Storage | Firestore | - | Long-term persistence |
| Natural Language | MCP Servers | 1.0 | Query interfaces |

## Memory Architecture

### Layered Memory System

1. **Short-term Memory (DragonflyDB)**
   - TTL: 1 hour (configurable)
   - Use case: Conversation context, working memory
   - Storage: 20Gi persistent volume

2. **Mid-term Memory (MongoDB)**
   - TTL: 1 day (configurable)
   - Use case: Session data, user preferences
   - Storage: 100Gi persistent volume

3. **Long-term Memory (Firestore)**
   - TTL: 30 days or permanent
   - Use case: User profiles, learned behaviors
   - Storage: Unlimited (GCP managed)

4. **Semantic Memory (Weaviate)**
   - No expiration
   - Use case: Vector search, similarity matching
   - Storage: As needed

## Infrastructure Components

### Pulumi Structure

```
infra/
├── main.py                    # Main orchestration
├── components/
│   ├── database_component.py  # Database resources
│   └── superagi_component.py  # SuperAGI deployment
├── requirements.txt           # Pulumi dependencies
└── Pulumi.yaml               # Project configuration
```

### Key Resources

1. **GKE Cluster**
   - Node pool: 2-10 nodes (autoscaling)
   - Machine type: n2-standard-4
   - Disk: 100GB SSD per node
   - Workload Identity enabled

2. **Kubernetes Resources**
   - Namespace: `superagi`
   - Deployments: SuperAGI, MCP servers
   - StatefulSets: MongoDB
   - Services: LoadBalancer for SuperAGI
   - ConfigMaps: Application configuration
   - Secrets: API keys, database credentials

3. **GCP Services**
   - Artifact Registry: Docker images
   - Secret Manager: Sensitive configuration
   - Firestore: Document storage
   - IAM: Service accounts and permissions

## Deployment

### Prerequisites

- GCP Project with billing enabled
- Python 3.10 installed
- Docker installed
- Pulumi account (free tier works)
- GitHub repository (for CI/CD)

### Automated Deployment

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export OPENROUTER_API_KEY="your-api-key"

# Run deployment script
./scripts/deploy_optimized_infrastructure.sh
```

This script handles:
- Environment setup
- GCP API enablement
- Pulumi stack initialization
- Docker image building
- Infrastructure deployment
- Kubernetes configuration
- Integration testing

### Manual Deployment

```bash
# Navigate to infrastructure directory
cd infra

# Install dependencies
pip install -r requirements.txt

# Initialize Pulumi stack
pulumi stack init dev
pulumi config set gcp_project_id $GCP_PROJECT_ID

# Deploy infrastructure
pulumi up

# Configure kubectl
gcloud container clusters get-credentials orchestra-cluster-dev \
  --zone=us-central1-a \
  --project=$GCP_PROJECT_ID
```

## CI/CD Pipeline

### GitHub Actions Workflow

Located at `.github/workflows/pulumi-deploy.yml`:

1. **Validation**: Linting, type checking, tests
2. **Preview**: On pull requests
3. **Deploy**: On push to main/develop
4. **Build**: Docker images to Artifact Registry
5. **Integration Tests**: Verify deployment

### Workload Identity Federation

Secure, keyless authentication:
- No service account keys in GitHub
- Automatic token generation
- Principle of least privilege

Setup with:
```bash
./scripts/setup_github_secrets.sh
```

## MCP Integration

Model Context Protocol servers provide natural language interfaces:

### MongoDB MCP
- Natural language queries: "Show all active agents"
- Automatic query translation
- Result formatting

### Weaviate MCP
- Semantic search: "Find similar documents"
- Vector similarity matching
- Context retrieval

### Usage Example
```python
from scripts.mcp_integration import MCPIntegration

mcp = MCPIntegration()
result = await mcp.query_mongodb("Show agents created this week")
```

## Monitoring and Operations

### Health Checks

```bash
# Test infrastructure
python scripts/test_infrastructure.py

# Check pod status
kubectl get pods -n superagi

# View logs
kubectl logs -f deployment/superagi -n superagi
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment/superagi --replicas=5 -n superagi

# Update autoscaling
pulumi config set superagi_replicas 5
pulumi up
```

### Cost Management

Estimated monthly costs:
- GKE cluster: $150-500
- Storage: $50
- Load Balancer: $20
- **Total: $220-570**

Cost optimization:
- Use preemptible nodes
- Scale down when idle
- Consider Cloud Run for lighter workloads

## Security

### Authentication
- Workload Identity for GCP services
- Kubernetes RBAC for cluster access
- API keys in Secret Manager

### Network Security
- Private GKE cluster option
- Network policies for pod communication
- HTTPS for all external endpoints

### Data Security
- Encryption at rest (GCP managed)
- Encryption in transit (TLS)
- Regular secret rotation

## Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod <pod-name> -n superagi
   kubectl logs <pod-name> -n superagi --previous
   ```

2. **MCP connection failed**
   ```bash
   kubectl get pods -n superagi | grep mcp
   kubectl logs deployment/mcp-mongodb -n superagi
   ```

3. **Pulumi deployment failed**
   ```bash
   pulumi stack export | jq '.deployment.resources[]'
   pulumi refresh --yes
   ```

### Debug Commands

```bash
# Check cluster status
kubectl cluster-info

# View all resources
kubectl get all -n superagi

# Check service endpoints
kubectl get svc -n superagi

# View Pulumi stack
pulumi stack output --json
```

## Maintenance

### Updates

1. **Update dependencies**
   ```bash
   cd infra
   pip install -U -r requirements.txt
   ```

2. **Update infrastructure**
   ```bash
   pulumi preview
   pulumi up
   ```

3. **Update images**
   ```bash
   docker build -t gcr.io/$PROJECT_ID/superagi:latest -f Dockerfile.superagi .
   docker push gcr.io/$PROJECT_ID/superagi:latest
   kubectl rollout restart deployment/superagi -n superagi
   ```

### Backup

- DragonflyDB: Automated snapshots to GCS
- MongoDB: Regular mongodump to GCS
- Firestore: GCP managed backups

### Disaster Recovery

1. **Infrastructure**: Pulumi state in GCS
2. **Data**: Regular backups to GCS
3. **Configuration**: All in Git

## Future Enhancements

1. **Multi-region deployment**
2. **Prometheus/Grafana monitoring**
3. **Automated backup strategies**
4. **Enhanced security policies**
5. **Cost optimization automation**

## References

- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [SuperAGI Documentation](https://docs.superagi.com)
- [MCP Specification](https://github.com/anthropics/mcp)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
