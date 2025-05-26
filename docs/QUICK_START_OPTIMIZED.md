# Quick Start Guide: Optimized AI Orchestra Infrastructure

## Overview

This guide will help you deploy the optimized AI Orchestra infrastructure with modular Pulumi components, automated CI/CD, and MCP integration in under 30 minutes.

## Prerequisites

- GCP Project with billing enabled
- Python 3.10 installed
- Docker installed
- GitHub repository (for CI/CD)
- Pulumi account (free tier works)

## Step 1: Initial Setup (5 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd orchestra-main

# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GITHUB_REPOSITORY="owner/repo"  # e.g., "myusername/orchestra-main"
export OPENROUTER_API_KEY="your-api-key"  # Get from OpenRouter

# Install GitHub CLI (if not installed)
# macOS: brew install gh
# Linux: See https://cli.github.com/
```

## Step 2: Deploy Infrastructure (15 minutes)

```bash
# Run the automated deployment script
./scripts/deploy_optimized_infrastructure.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Set up Python environment
- ✅ Configure GCP APIs
- ✅ Initialize Pulumi stack
- ✅ Build and push Docker images
- ✅ Deploy infrastructure
- ✅ Configure kubectl
- ✅ Run integration tests

## Step 3: Configure GitHub Actions (5 minutes)

```bash
# Set up GitHub secrets for CI/CD
./scripts/setup_github_secrets.sh
```

This will:
- Configure Workload Identity Federation (no service account keys!)
- Set up GitHub repository secrets
- Enable automated deployments on push

## Step 4: Test MCP Integration (5 minutes)

```bash
# Port forward to test locally
kubectl port-forward svc/mcp-mongodb 8081:8080 -n superagi &
kubectl port-forward svc/mcp-weaviate 8082:8080 -n superagi &

# Test MCP integration
python scripts/mcp_integration.py
```

Example queries you can now run:
- "Show all active agents created this week"
- "Find conversations about API integration"
- "Search for documents similar to machine learning optimization"

## Step 5: Use Cursor AI Effectively

1. Copy the `.cursorrules` content from `docs/CURSOR_AI_OPTIMIZATION_GUIDE.md` to your project root
2. Use these power prompts:

```
# Generate a new Pulumi component
Write a Pulumi component for Prometheus monitoring that follows the pattern in infra/components/database_component.py

# Add MCP support for a new data source
Implement MCP server integration for Redis following the pattern in scripts/mcp_integration.py

# Debug infrastructure issues
Analyze why pods are failing in the superagi namespace and provide kubectl commands to fix
```

## Architecture Overview

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

## Common Commands

```bash
# View all resources
kubectl get all -n superagi

# Check logs
kubectl logs -f deployment/superagi -n superagi

# Access SuperAGI locally
kubectl port-forward svc/superagi 8080:8080 -n superagi

# Update infrastructure
cd infra && pulumi up

# Destroy everything
cd infra && pulumi destroy
```

## Troubleshooting

### Issue: Pods not starting
```bash
kubectl describe pod <pod-name> -n superagi
kubectl logs <pod-name> -n superagi --previous
```

### Issue: MCP connection failed
```bash
# Check MCP server status
kubectl get pods -n superagi | grep mcp
kubectl logs deployment/mcp-mongodb -n superagi
```

### Issue: Pulumi deployment failed
```bash
# Check Pulumi state
pulumi stack export | jq '.deployment.resources[] | select(.type == "kubernetes:apps/v1:Deployment")'

# Refresh state
pulumi refresh --yes
```

## Cost Optimization

Current setup costs (estimated):
- GKE cluster (2-10 nodes): ~$150-500/month
- Storage (SSD): ~$50/month
- Load Balancer: ~$20/month
- **Total: ~$220-570/month**

To reduce costs:
1. Use preemptible nodes: Add `preemptible: true` to node config
2. Scale down when not in use: `kubectl scale deployment --all --replicas=0 -n superagi`
3. Use Cloud Run instead of GKE for lighter workloads

## Next Steps

1. **Configure Agents**: Access SuperAGI UI and create your AI agents
2. **Set up Monitoring**: Deploy Prometheus/Grafana (see `docs/monitoring/`)
3. **Add Custom MCP Servers**: Extend `scripts/mcp_integration.py`
4. **Optimize Prompts**: Use Cursor AI guide for faster development

## Support

- Documentation: `docs/`
- Integration Tests: `tests/integration/`
- Cursor AI Guide: `docs/CURSOR_AI_OPTIMIZATION_GUIDE.md`

Remember: This setup prioritizes simplicity and performance over enterprise complexity. Keep it lean!
