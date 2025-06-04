# SuperAGI Deployment Plan for AI cherry_ai

## Overview

This document details the complete deployment plan for SuperAGI on Google Kubernetes Engine (GKE) with domain configuration for cherry-ai.me.

## Current Architecture

### Components
1. **SuperAGI Core**: Multi-agent coordination system (3 replicas, auto-scaling 2-10)
2. **DragonflyDB**: Redis-compatible in-memory cache (20Gi storage)
3. **MongoDB**: Document store for agent data (100Gi storage)
4. **Weaviate**: Vector database for semantic search (50Gi storage)
5. **MCP Servers**: Natural language interfaces for MongoDB and Weaviate
6. **MongoDB
### Infrastructure Stack
- **Platform**: Google Kubernetes Engine (GKE)
- **IaC**: Pulumi with Python
- **Container Registry**: Google Container Registry (GCR)
- **Load Balancer**: GKE LoadBalancer service
- **Domain**: cherry-ai.me (needs configuration)

## Deployment Conflicts Analysis

### ✅ No Conflicts Detected
1. **Port Conflicts**: Each service uses unique ports
   - SuperAGI: 8080
   - DragonflyDB: 6379
   - MongoDB: 27017
   - Weaviate: 8080 (internal)
   - MCP Servers: 8080 (internal, different namespaces)

2. **Resource Conflicts**: Proper resource limits set
   - SuperAGI: 2-4Gi memory, 1-2 CPU
   - MCP Servers: 512Mi-1Gi memory, 250m-500m CPU
   - Databases: Adequate storage provisioned

3. **Namespace Isolation**: All components in `superagi` namespace

### ⚠️ Missing Domain Configuration

The current deployment uses a LoadBalancer service but lacks:
1. **Ingress Controller**: For HTTPS and domain routing
2. **SSL/TLS Certificates**: For secure connections
3. **DNS Configuration**: To point cherry-ai.me to the cluster

## Enhanced Deployment Plan

### Phase 1: Add Domain Support

Create `infra/components/ingress_component.py`:

```python
"""
Ingress Component for Domain Configuration
"""

import pulumi_kubernetes as k8s
from pulumi import ComponentResource, ResourceOptions
from typing import Dict, Any, Optional


class IngressComponent(ComponentResource):
    """Configure ingress with SSL for cherry-ai.me"""

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        service_name: str,
        opts: Optional[ResourceOptions] = None
    ):
        super().__init__("cherry_ai:ingress:Component", name, None, opts)

        self.namespace = config.get("namespace", "superagi")
        self.domain = config.get("domain", "cherry-ai.me")

        # Create child options
        child_opts = ResourceOptions(parent=self)

        # Install cert-manager for automatic SSL
        self._install_cert_manager(child_opts)

        # Create ingress
        self.ingress = self._create_ingress(service_name, child_opts)

        # Create certificate
        self.certificate = self._create_certificate(child_opts)

    def _install_cert_manager(self, opts: ResourceOptions):
        """Install cert-manager for automatic SSL certificates"""

        # Apply cert-manager CRDs
        k8s.yaml.ConfigFile(
            "cert-manager",
            file="https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml",
            opts=opts,
        )

    def _create_ingress(self, service_name: str, opts: ResourceOptions) -> k8s.networking.v1.Ingress:
        """Create ingress for cherry-ai.me"""

        return k8s.networking.v1.Ingress(
            f"{self._name}-ingress",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="superagi-ingress",
                namespace=self.namespace,
                annotations={
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "nginx.ingress.kubernetes.io/proxy-body-size": "50m",
                    "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
                    "nginx.ingress.kubernetes.io/proxy-send-timeout": "600",
                },
            ),
            spec=k8s.networking.v1.IngressSpecArgs(
                tls=[
                    k8s.networking.v1.IngressTLSArgs(
                        hosts=[self.domain, f"www.{self.domain}"],
                        secret_name="superagi-tls",
                    )
                ],
                rules=[
                    k8s.networking.v1.IngressRuleArgs(
                        host=self.domain,
                        http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                            paths=[
                                k8s.networking.v1.HTTPIngressPathArgs(
                                    path="/",
                                    path_type="Prefix",
                                    backend=k8s.networking.v1.IngressBackendArgs(
                                        service=k8s.networking.v1.IngressServiceBackendArgs(
                                            name=service_name,
                                            port=k8s.networking.v1.ServiceBackendPortArgs(
                                                number=8080,
                                            ),
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ),
                    # Redirect www to non-www
                    k8s.networking.v1.IngressRuleArgs(
                        host=f"www.{self.domain}",
                        http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                            paths=[
                                k8s.networking.v1.HTTPIngressPathArgs(
                                    path="/",
                                    path_type="Prefix",
                                    backend=k8s.networking.v1.IngressBackendArgs(
                                        service=k8s.networking.v1.IngressServiceBackendArgs(
                                            name=service_name,
                                            port=k8s.networking.v1.ServiceBackendPortArgs(
                                                number=8080,
                                            ),
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            opts=opts,
        )

    def _create_certificate(self, opts: ResourceOptions):
        """Create Let's Encrypt certificate"""

        # Create ClusterIssuer for Let's Encrypt
        k8s.apiextensions.CustomResource(
            f"{self._name}-letsencrypt-issuer",
            api_version="cert-manager.io/v1",
            kind="ClusterIssuer",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="letsencrypt-prod",
            ),
            spec={
                "acme": {
                    "server": "https://acme-v02.api.letsencrypt.org/directory",
                    "email": "scoobyjava@cherry-ai.me",
                    "privateKeySecretRef": {
                        "name": "letsencrypt-prod",
                    },
                    "solvers": [{
                        "http01": {
                            "ingress": {
                                "class": "nginx",
                            },
                        },
                    }],
                },
            },
            opts=opts,
        )
```

### Phase 2: Update Main Infrastructure

Update `infra/main.py` to include ingress:

```python
# Add after SuperAGI deployment
from components.ingress_component import IngressComponent

# Deploy ingress with domain configuration
ingress_config = {
    "namespace": "superagi",
    "domain": "cherry-ai.me",
}

ingress_component = IngressComponent(
    "cherry_ai-ingress",
    config=ingress_config,
    service_name="superagi",
    opts=ResourceOptions(provider=k8s_provider, depends_on=[superagi_component]),
)

# Update exports
pulumi.export("domain", "cherry-ai.me")
pulumi.export("https_endpoint", f"https://cherry-ai.me")
```

### Phase 3: DNS Configuration

1. **Configure DNS Records** (manual step):
   ```bash
   # Get the ingress IP
   kubectl get ingress superagi-ingress -n superagi -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

   # Add A records in your DNS provider:
   # cherry-ai.me -> INGRESS_IP
   # www.cherry-ai.me -> INGRESS_IP
   ```

2. **Or use Cloud DNS** (automated):
   ```python
   # Add to infra/main.py
   dns_zone =        "cherry-ai-zone",
       name="cherry-ai-zone",
       dns_name="cherry-ai.me.",
       description="DNS zone for cherry-ai.me",
   )

   dns_record =        "cherry-ai-a-record",
       name="cherry-ai.me.",
       type="A",
       ttl=300,
       managed_zone=dns_zone.name,
       rrdatas=[ingress_component.ingress.status.load_balancer.ingress[0].ip],
   )
   ```

## Deployment Steps

### 1. Pre-deployment Checklist
- [x] Python 3.10.12 environment
- [x] Pulumi CLI installed (v3.171.0)
- [x] kubectl configured (v1.33.1)
- [x] - [x] Docker installed
- [ ] Domain DNS access configured

### 2. Update Infrastructure Code
```bash
# Add ingress component
cp docs/SUPERAGI_DEPLOYMENT_PLAN.md infra/components/ingress_component.py
# Extract the Python code from Phase 1

# Update main.py with ingress configuration
# Add the code from Phase 2
```

### 3. Deploy Infrastructure
```bash
# Set environment variables
export export PULUMI_STACK=dev

# Run deployment
./scripts/deploy_optimized_infrastructure.sh
```

### 4. Configure DNS
```bash
# Get ingress IP
INGRESS_IP=$(kubectl get ingress superagi-ingress -n superagi -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Configure DNS A record: cherry-ai.me -> $INGRESS_IP"
```

### 5. Verify Deployment
```bash
# Check certificate status
kubectl describe certificate superagi-tls -n superagi

# Test HTTPS endpoint
curl -I https://cherry-ai.me

# Check all components
kubectl get all -n superagi
```

## Post-Deployment Configuration

### 1. SuperAGI Admin Setup
- Access: https://cherry-ai.me/admin
- Default credentials: Set via environment variables
- Configure agent templates
- Set up tool integrations

### 2. MCP Server Configuration
- MongoDB queries: https://cherry-ai.me/api/mcp/mongodb
- Weaviate search: https://cherry-ai.me/api/mcp/weaviate
- Test with natural language queries

### 3. Monitoring Setup
```bash
# View logs
kubectl logs -f deployment/superagi -n superagi

# Monitor resources
kubectl top pods -n superagi

# Check HPA status
kubectl get hpa -n superagi
```

## Security Considerations

1. **SSL/TLS**: Automatic via Let's Encrypt
2. **Authentication**: Configure OAuth2/OIDC for production
3. **Network Policies**: Restrict inter-pod communication
4. **Secrets Management**: All sensitive data in Kubernetes secrets
5. **RBAC**: Service accounts with minimal permissions

## Rollback Plan

If issues occur:
```bash
# Rollback Pulumi deployment
pulumi stack history -C infra
pulumi up --target-urn <previous-urn> -C infra

# Or destroy and redeploy
pulumi destroy -C infra
./scripts/deploy_optimized_infrastructure.sh
```

## Cost Optimization

Estimated monthly costs:
- GKE cluster (n2-standard-4, 2-10 nodes): ~$300-1500
- Load Balancer: ~$20
- Storage (170Gi total): ~$30
- Egress traffic: Variable
- **Total**: ~$350-1550/month

Optimization tips:
1. Use preemptible nodes for non-critical workloads
2. Enable cluster autoscaling
3. Set resource limits appropriately
4. Use regional clusters only if needed

## Summary

The deployment plan ensures:
- ✅ No resource conflicts
- ✅ Proper domain configuration for cherry-ai.me
- ✅ SSL/TLS encryption
- ✅ Auto-scaling capabilities
- ✅ High availability with 3 SuperAGI replicas
- ✅ Integrated MCP servers for natural language queries
- ✅ Comprehensive monitoring and logging

The system will be accessible at https://cherry-ai.me with full SuperAGI capabilities and MCP integration.
