# Cherry AI Infrastructure - Pulumi IaC

This directory contains the Infrastructure as Code (IaC) for deploying the Cherry AI Admin Interface on Vultr using Pulumi with Python.

## Architecture Overview

The infrastructure includes:
- **VPC**: Private network isolation for all resources
- **Kubernetes Cluster**: Container orchestration with auto-scaling
- **PostgreSQL**: Managed database with vector extensions
- **Redis**: Managed cache for performance optimization
- **Load Balancer**: High availability with SSL termination
- **Object Storage**: Static assets and backups
- **Monitoring**: Prometheus + Grafana stack

## Prerequisites

1. **Pulumi CLI**: Install from [pulumi.com](https://www.pulumi.com/docs/get-started/install/)
2. **Python 3.8+**: Required for Pulumi Python runtime
3. **Vultr API Key**: Set as environment variable
4. **kubectl**: For Kubernetes management

## Environment Setup

1. **Set Vultr API Key**:
   ```bash
   export VULTR_API_KEY="your-vultr-api-key"
   ```

2. **Install Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Login to Pulumi**:
   ```bash
   # For Pulumi Cloud (recommended)
   pulumi login
   
   # For local state
   pulumi login --local
   ```

## Deployment

### Quick Start

Deploy to development environment:
```bash
python deploy.py deploy --stack dev
```

### Available Commands

```bash
# Preview changes before deployment
python deploy.py preview --stack <env>

# Deploy infrastructure
python deploy.py deploy --stack <env> [--auto-approve]

# Export outputs (kubeconfig, IPs, etc.)
python deploy.py export --stack <env>

# Rollback to previous deployment
python deploy.py rollback --stack <env>

# Destroy infrastructure
python deploy.py destroy --stack <env> [--auto-approve]
```

### Environment Stacks

- **dev**: Development environment (minimal resources)
- **staging**: Staging environment (production-like)
- **prod**: Production environment (high availability)

## Stack Configuration

Each environment has its own configuration file:
- `Pulumi.dev.yaml`: Development configuration
- `Pulumi.staging.yaml`: Staging configuration
- `Pulumi.prod.yaml`: Production configuration

### Customizing Configuration

Override default values:
```bash
pulumi config set cherry-ai-infrastructure:region sjc  # Change region
pulumi config set cherry-ai-infrastructure:k8s_node_plan vc2-4c-8gb  # Larger nodes
```

## Post-Deployment Steps

### 1. Configure DNS

Point your domain to the load balancer IP:
```bash
# Get load balancer IP
pulumi stack output load_balancer_ip
```

### 2. Access Kubernetes

```bash
# Export kubeconfig
pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
export KUBECONFIG=./kubeconfig.yaml

# Verify connection
kubectl get nodes
```

### 3. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f ../../k8s/

# Check deployment status
kubectl get pods -n cherry-ai
```

### 4. Access Monitoring

```bash
# Get monitoring IP
pulumi stack output monitoring_ip

# Access Grafana
open http://<monitoring-ip>:3000
# Default credentials: admin/admin
```

## Blue-Green Deployment

The infrastructure supports blue-green deployments:

1. **Deploy Green Environment**:
   ```bash
   pulumi stack init prod-green
   pulumi up --stack prod-green
   ```

2. **Test Green Environment**:
   - Verify application functionality
   - Run smoke tests
   - Check monitoring metrics

3. **Switch Traffic**:
   - Update DNS to point to green load balancer
   - Monitor for issues

4. **Cleanup Blue Environment**:
   ```bash
   pulumi destroy --stack prod-blue
   ```

## Disaster Recovery

### Backup Strategy

1. **Database Backups**:
   - Automated daily backups (retained for 7 days)
   - Point-in-time recovery available

2. **Object Storage**:
   - Cross-region replication enabled
   - Versioning for all objects

3. **Infrastructure State**:
   - Pulumi state backed up to cloud
   - Version controlled configuration

### Recovery Procedures

1. **Database Recovery**:
   ```bash
   # Restore from backup
   vultr database restore <backup-id>
   ```

2. **Full Infrastructure Recovery**:
   ```bash
   # Deploy from scratch
   python deploy.py deploy --stack prod --auto-approve
   ```

## Monitoring and Alerts

### Available Metrics

- **Kubernetes**: Node/pod health, resource usage
- **Database**: Connections, query performance
- **Redis**: Hit rate, memory usage
- **Load Balancer**: Request rate, latency

### Setting Up Alerts

1. Access Grafana dashboard
2. Navigate to Alerting → Alert Rules
3. Create alerts for:
   - High CPU/memory usage
   - Database connection limits
   - Application errors
   - SSL certificate expiration

## Cost Optimization

### Resource Sizing

| Environment | Monthly Cost (Est.) | Use Case |
|------------|-------------------|----------|
| Dev        | ~$50              | Development/testing |
| Staging    | ~$150             | Pre-production testing |
| Production | ~$500             | Live traffic |

### Cost Saving Tips

1. **Auto-scaling**: Configure min/max nodes appropriately
2. **Dev Environment**: Destroy when not in use
3. **Object Storage**: Set lifecycle policies
4. **Monitoring**: Use single instance for non-prod

## Troubleshooting

### Common Issues

1. **Deployment Fails**:
   ```bash
   # Check Pulumi logs
   pulumi logs --stack <env>
   
   # Verify API key
   echo $VULTR_API_KEY
   ```

2. **Cannot Connect to Kubernetes**:
   ```bash
   # Re-export kubeconfig
   pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
   
   # Check cluster status
   vultr kubernetes list
   ```

3. **Database Connection Issues**:
   ```bash
   # Check VPC connectivity
   # Ensure app is in same VPC
   ```

## Security Best Practices

1. **Secrets Management**:
   - Never commit secrets to git
   - Use Pulumi secrets for sensitive data
   - Rotate credentials regularly

2. **Network Security**:
   - All resources in private VPC
   - Firewall rules restrict access
   - SSL/TLS for all public endpoints

3. **Access Control**:
   - Use kubectl RBAC
   - Limit database access
   - Enable audit logging

## Contributing

1. **Making Changes**:
   - Create feature branch
   - Test in dev environment
   - Submit PR with preview

2. **Code Standards**:
   - Follow Python PEP 8
   - Document all functions
   - Add type hints

3. **Testing**:
   ```bash
   # Run linting
   pylint *.py
   
   # Test deployment
   python deploy.py preview --stack dev
   ```

## Support

- **Documentation**: See `/docs` directory
- **Issues**: Create GitHub issue
- **Vultr Support**: support.vultr.com
- **Pulumi Support**: pulumi.com/support

## License

This infrastructure code is part of the Cherry AI project and follows the same license terms.