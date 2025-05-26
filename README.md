# AI Orchestra

AI Orchestra is a comprehensive AI agent orchestration platform that integrates SuperAGI with managed cloud services for scalable, production-ready deployments.

## Quick Start

Deploy AI Orchestra with one command:

```bash
./scripts/deploy_simple.sh
```

This deploys:
- SuperAGI agent framework
- MongoDB Atlas for persistent storage
- DragonflyDB Cloud for high-performance caching (12.5GB)
- Weaviate Cloud for semantic search
- Optional monitoring stack (Prometheus + Grafana)

## Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and authenticated
- `kubectl` installed
- `pulumi` installed
- Python 3.10

## Deployment Options

### Development Deployment
```bash
./scripts/deploy_simple.sh dev
```

### Production Deployment
```bash
./scripts/deploy_simple.sh prod
```

### Custom Deployment
For more control, use the main deployment script:
```bash
ENVIRONMENT=prod REGION=us-east1 ./scripts/deploy_orchestra.sh
```

## Architecture

AI Orchestra uses:
- **GKE** for container orchestration
- **SuperAGI** for agent execution
- **MongoDB Atlas** for document storage
- **DragonflyDB Cloud** for caching (Redis-compatible)
- **Weaviate Cloud** for vector search
- **Pulumi** for infrastructure as code

## Post-Deployment

After deployment, you can:

1. **Access SuperAGI locally**:
   ```bash
   kubectl port-forward -n ai-orchestra svc/ai-orchestra 8080:8080
   ```
   Then open http://localhost:8080

2. **View logs**:
   ```bash
   kubectl logs -f deployment/ai-orchestra -n ai-orchestra
   ```

3. **Check deployment status**:
   ```bash
   kubectl get all -n ai-orchestra
   ```

## Documentation

- [Deployment Scripts Guide](docs/DEPLOYMENT_SCRIPTS_GUIDE.md)
- [SuperAGI Integration](SUPERAGI_INTEGRATION.md)
- [Enhancement Guide](docs/SUPERAGI_ENHANCEMENTS.md)

## Cleanup

To remove all resources:
```bash
cd infra
pulumi destroy --yes
```

## Support

For issues or questions, please check the documentation or create an issue in the repository.
