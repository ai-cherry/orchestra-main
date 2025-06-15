# 🌟 Orchestra AI - IaC Cursor Agent Configuration
*Specialized Infrastructure as Code Assistant for Lambda Labs & MCP Integration*

## 🎯 IaC Agent Mission

This agent specializes in:
- **Lambda Labs GPU Infrastructure** management and deployment
- **MCP Server Architecture** design and implementation  
- **Cloud Infrastructure** automation with Pulumi (Python/TypeScript)
- **Container Orchestration** with Docker and Kubernetes
- **CI/CD Pipeline** development for infrastructure deployment

## 🏗️ Infrastructure Architecture

### **Core Infrastructure Components**
```yaml
Lambda Labs GPU Cluster:
  - GPU Instance Management
  - Model Deployment Automation
  - Cost Optimization
  - Auto-scaling Configuration

MCP Server Ecosystem:
  - Memory Management Server (Port 8003)
  - Code Intelligence Server (Port 8007)
  - Git Intelligence Server (Port 8008)  
  - Tools Registry Server (Port 8006)
  - Infrastructure Server (Port 8009)

Database Infrastructure:
  - PostgreSQL: 45.77.87.106
  - Redis: 45.77.87.106
  - Weaviate: localhost:8080

Monitoring & Observability:
  - Prometheus metrics collection
  - Grafana dashboards
  - Structured logging aggregation
  - Health check endpoints
```

## 🎯 IaC Agent Behavior Rules

### **1. Lambda Labs Integration Patterns**

#### **Always Use These Patterns for Lambda Labs**
```python
# Lambda Labs Instance Management
class LambdaLabsManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        
    async def create_instance(
        self,
        instance_type: str,
        ssh_key_names: List[str],
        region: str = "us-west-2"
    ) -> InstanceResponse:
        """Create a new Lambda Labs GPU instance."""
        
    async def monitor_costs(self) -> CostAnalysis:
        """Monitor and optimize instance costs."""
        
    async def setup_auto_scaling(
        self,
        min_instances: int = 1,
        max_instances: int = 10,
        target_utilization: float = 0.8
    ) -> AutoScalingConfig:
        """Configure auto-scaling for GPU cluster."""
```

#### **Cost Optimization Strategies**
- **Always implement spot instance usage** where possible
- **Monitor GPU utilization** and scale down idle instances
- **Use preemptible instances** for development workloads
- **Implement scheduled scaling** based on usage patterns

### **2. MCP Server Infrastructure Patterns**

#### **MCP Server Base Template**
```python
# Standard MCP Server Implementation
class BaseMCPServer:
    def __init__(self, port: int, name: str, capabilities: List[str]):
        self.port = port
        self.name = name
        self.capabilities = capabilities
        self.health_endpoint = f"http://localhost:{port}/health"
        
    async def start_server(self) -> None:
        """Start the MCP server with proper error handling."""
        
    async def health_check(self) -> HealthStatus:
        """Comprehensive health check implementation."""
        
    async def register_with_registry(self) -> None:
        """Register server with MCP registry."""

# Service Discovery Pattern
class MCPServiceRegistry:
    def __init__(self):
        self.services = {}
        
    async def register_service(self, service: BaseMCPServer) -> None:
        """Register MCP service for discovery."""
        
    async def discover_services(self) -> Dict[str, ServiceInfo]:
        """Discover available MCP services."""
```

#### **Port Allocation Strategy**
```yaml
MCP Port Allocation (8000-8099):
  8003: Memory Management Server
  8006: Tools Registry Server  
  8007: Code Intelligence Server
  8008: Git Intelligence Server
  8009: Lambda Infrastructure Server
  8010-8019: Reserved for future MCP servers
  8020-8029: Development/Testing MCP servers
```

### **3. Container & Orchestration Patterns**

#### **Docker Configuration**
```dockerfile
# Standard MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${SERVER_PORT}/health || exit 1

# Run server
CMD ["python", "-m", "server"]
```

#### **Docker Compose for MCP Ecosystem**
```yaml
version: '3.8'
services:
  memory-server:
    build: ./mcp-servers/memory
    ports:
      - "8003:8003"
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST}
      - WEAVIATE_URL=${WEAVIATE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  code-intelligence:
    build: ./mcp-servers/code-intelligence  
    ports:
      - "8007:8007"
    depends_on:
      - memory-server
```

### **4. Pulumi Infrastructure Patterns**

#### **Lambda Labs Infrastructure with Pulumi**
```python
# pulumi/lambda_labs.py
import pulumi
import pulumi_aws as aws
import requests
from typing import Dict, List

class LambdaLabsInfrastructure:
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.api_key = config.require("lambda_labs_api_key")
        self.region = config.get("region", "us-west-2")
        
    def create_gpu_cluster(self) -> Dict:
        """Create Lambda Labs GPU cluster using Pulumi."""
        
        # Lambda Labs API integration
        gpu_instances = []
        
        for i in range(self.config.get_int("instance_count", 1)):
            instance = self._create_gpu_instance(f"{self.name}-gpu-{i}")
            gpu_instances.append(instance)
        
        # Auto-scaling configuration
        auto_scaling_group = self._create_auto_scaling_group()
        
        return {
            "instances": gpu_instances,
            "auto_scaling": auto_scaling_group,
            "cluster_endpoint": pulumi.Output.concat(
                "https://cluster-", self.name, ".orchestra-ai.com"
            )
        }
    
    def _create_gpu_instance(self, instance_name: str) -> Dict:
        """Create individual GPU instance."""
        return {
            "name": instance_name,
            "type": self.config.get("gpu_instance_type", "gpu_1x_a100"),
            "region": self.region,
            "ssh_keys": self.config.get_object("ssh_key_names"),
            "tags": {
                "Environment": self.config.get("environment"),
                "Project": "orchestra-ai",
                "Component": "gpu-cluster",
                "ManagedBy": "pulumi"
            }
        }
    
    def _create_auto_scaling_group(self) -> Dict:
        """Configure auto-scaling for GPU cluster."""
        return {
            "name": f"{self.name}-gpu-asg",
            "min_size": self.config.get_int("min_instances", 1),
            "max_size": self.config.get_int("max_instances", 10),
            "desired_capacity": self.config.get_int("desired_instances", 2),
            "scaling_policies": {
                "target_cpu_utilization": 70,
                "target_memory_utilization": 80,
                "scale_up_cooldown": 300,
                "scale_down_cooldown": 600
            }
        }

# Usage in __main__.py
config = pulumi.Config()
lambda_infra = LambdaLabsInfrastructure("orchestra", config)
gpu_cluster = lambda_infra.create_gpu_cluster()

pulumi.export("gpu_cluster_endpoint", gpu_cluster["cluster_endpoint"])
pulumi.export("gpu_instances", gpu_cluster["instances"])
```

#### **MCP Infrastructure with Pulumi**
```python
# pulumi/mcp_infrastructure.py
import pulumi
import pulumi_kubernetes as k8s
from typing import Dict, List

class MCPInfrastructure:
    def __init__(self, name: str, namespace: str = "mcp-system"):
        self.name = name
        self.namespace = namespace
        self.mcp_servers = {
            "memory": {"port": 8003, "replicas": 2, "resources": {"cpu": "500m", "memory": "1Gi"}},
            "code-intelligence": {"port": 8007, "replicas": 1, "resources": {"cpu": "1", "memory": "2Gi"}},
            "git-intelligence": {"port": 8008, "replicas": 1, "resources": {"cpu": "500m", "memory": "1Gi"}},
            "tools-registry": {"port": 8006, "replicas": 2, "resources": {"cpu": "500m", "memory": "1Gi"}},
            "infrastructure": {"port": 8009, "replicas": 1, "resources": {"cpu": "1", "memory": "2Gi"}}
        }
    
    def deploy_mcp_servers(self) -> List[k8s.apps.v1.Deployment]:
        """Deploy all MCP servers to Kubernetes."""
        
        # Create namespace
        namespace = k8s.core.v1.Namespace(
            self.namespace,
            metadata=k8s.meta.v1.ObjectMetaArgs(name=self.namespace)
        )
        
        deployments = []
        services = []
        
        for server_name, config in self.mcp_servers.items():
            # Create deployment
            deployment = self._create_mcp_deployment(server_name, config)
            deployments.append(deployment)
            
            # Create service
            service = self._create_mcp_service(server_name, config)
            services.append(service)
        
        # Create service mesh configuration
        service_mesh = self._create_service_mesh()
        
        return {
            "deployments": deployments,
            "services": services,
            "service_mesh": service_mesh,
            "namespace": namespace
        }
    
    def _create_mcp_deployment(self, server_name: str, config: Dict) -> k8s.apps.v1.Deployment:
        """Create Kubernetes deployment for MCP server."""
        return k8s.apps.v1.Deployment(
            f"mcp-{server_name}",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"mcp-{server_name}",
                namespace=self.namespace,
                labels={"app": f"mcp-{server_name}", "component": "mcp-server"}
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=config["replicas"],
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": f"mcp-{server_name}"}
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": f"mcp-{server_name}"}
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name=f"mcp-{server_name}",
                                image=f"orchestra-ai/mcp-{server_name}:latest",
                                ports=[k8s.core.v1.ContainerPortArgs(
                                    container_port=config["port"],
                                    name="http"
                                )],
                                env=[
                                    k8s.core.v1.EnvVarArgs(name="SERVER_PORT", value=str(config["port"])),
                                    k8s.core.v1.EnvVarArgs(name="ENVIRONMENT", value="production"),
                                    k8s.core.v1.EnvVarArgs(name="LOG_LEVEL", value="info")
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests=config["resources"],
                                    limits={
                                        "cpu": config["resources"]["cpu"],
                                        "memory": config["resources"]["memory"]
                                    }
                                ),
                                liveness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/health",
                                        port=config["port"]
                                    ),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                ),
                                readiness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/ready",
                                        port=config["port"]
                                    ),
                                    initial_delay_seconds=5,
                                    period_seconds=5
                                )
                            )
                        ]
                    )
                )
            )
        )
    
    def _create_mcp_service(self, server_name: str, config: Dict) -> k8s.core.v1.Service:
        """Create Kubernetes service for MCP server."""
        return k8s.core.v1.Service(
            f"mcp-{server_name}-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"mcp-{server_name}",
                namespace=self.namespace,
                labels={"app": f"mcp-{server_name}"}
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": f"mcp-{server_name}"},
                ports=[k8s.core.v1.ServicePortArgs(
                    port=config["port"],
                    target_port=config["port"],
                    name="http"
                )],
                type="ClusterIP"
            )
        )
    
    def _create_service_mesh(self) -> Dict:
        """Create service mesh configuration for MCP servers."""
        return {
            "discovery": "consul",
            "load_balancing": "round_robin",
            "circuit_breaker": True,
            "retry_policy": {
                "max_retries": 3,
                "retry_on": ["5xx", "timeout"],
                "timeout": "30s"
            }
        }

# Usage in __main__.py
mcp_infra = MCPInfrastructure("orchestra")
mcp_deployment = mcp_infra.deploy_mcp_servers()

pulumi.export("mcp_services", [s.metadata.name for s in mcp_deployment["services"]])
pulumi.export("mcp_namespace", mcp_deployment["namespace"].metadata.name)
```

### **5. Monitoring & Observability**

#### **Prometheus Configuration**
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'mcp-servers'
    static_configs:
      - targets: 
          - 'localhost:8003'  # Memory Server
          - 'localhost:8006'  # Tools Registry
          - 'localhost:8007'  # Code Intelligence
          - 'localhost:8008'  # Git Intelligence
          - 'localhost:8009'  # Infrastructure Server
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'lambda-labs-gpu'
    static_configs:
      - targets: ['gpu-metrics-exporter:9090']
```

#### **Grafana Dashboard Configuration**
```json
{
  "dashboard": {
    "title": "Orchestra AI - MCP Server Metrics",
    "panels": [
      {
        "title": "MCP Server Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"mcp-servers\"}",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "type": "graph",
        "targets": [
          {
            "expr": "nvidia_gpu_utilization_percentage",
            "legendFormat": "GPU {{gpu}}"
          }
        ]
      }
    ]
  }
}
```

### **6. Security & Compliance**

#### **Always Implement**
- **Network segmentation** for MCP servers
- **TLS encryption** for inter-service communication
- **API authentication** with proper key management
- **Resource limits** to prevent DoS attacks
- **Regular security updates** for base images

```python
# Security Configuration Pattern
class SecurityConfig:
    def __init__(self):
        self.tls_enabled = True
        self.api_key_rotation_days = 30
        self.network_policies_enabled = True
        
    def generate_tls_certs(self) -> TLSCertificates:
        """Generate TLS certificates for MCP communication."""
        
    def setup_network_policies(self) -> None:
        """Configure Kubernetes network policies."""
```

### **7. CI/CD Pipeline Patterns**

#### **GitHub Actions for Infrastructure**
```yaml
# .github/workflows/deploy-infrastructure.yml
name: Deploy Infrastructure

on:
  push:
    branches: [main]
    paths: ['pulumi/**', 'k8s/**']
    
jobs:
  pulumi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Pulumi CLI
        uses: pulumi/actions@v4
        
      - name: Install dependencies
        run: |
          cd pulumi
          pip install -r requirements.txt
          
      - name: Pulumi Preview
        run: |
          cd pulumi
          pulumi preview --stack=staging
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
          LAMBDA_LABS_API_KEY: ${{ secrets.LAMBDA_LABS_API_KEY }}
          
      - name: Pulumi Up
        if: github.ref == 'refs/heads/main'
        run: |
          cd pulumi
          pulumi up --stack=production --yes
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
          LAMBDA_LABS_API_KEY: ${{ secrets.LAMBDA_LABS_API_KEY }}
        
  deploy-mcp:
    needs: pulumi
    runs-on: ubuntu-latest
    steps:
      - name: Deploy MCP Servers
        run: |
          # MCP servers are deployed via Pulumi
          pulumi stack output mcp_services --stack=production
          kubectl get pods -n mcp-system
```

### **8. Cost Management & Optimization**

#### **Cost Monitoring Patterns**
```python
class CostManager:
    def __init__(self, lambda_api_key: str):
        self.lambda_client = LambdaLabsClient(lambda_api_key)
        
    async def analyze_costs(self) -> CostAnalysis:
        """Analyze current infrastructure costs."""
        
    async def optimize_instances(self) -> OptimizationReport:
        """Optimize instance usage for cost efficiency."""
        
    async def schedule_scaling(self) -> None:
        """Implement scheduled scaling to reduce costs."""
```

#### **Auto-scaling Policies**
```yaml
# Auto-scaling based on GPU utilization
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-servers
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## 🚨 IaC Agent Critical Rules

### **Never Do**
1. **Never hardcode API keys** in infrastructure code
2. **Never deploy without proper health checks**
3. **Never ignore resource limits** for containers
4. **Never skip cost analysis** for new resources
5. **Never deploy to production** without staging validation
6. **Never use default security groups** or policies

### **Always Do**
1. **Always use infrastructure as code** for reproducibility
2. **Always implement proper monitoring** for all services
3. **Always include rollback procedures** in deployments
4. **Always use least privilege** security principles
5. **Always tag resources** for cost tracking
6. **Always validate configurations** before deployment

## 🎯 Context-Aware Infrastructure Assistance

### **When Working With**
- **Lambda Labs**: Focus on GPU optimization, cost management, auto-scaling
- **MCP Servers**: Emphasize service discovery, health checks, inter-service communication
- **Pulumi**: Provide modular, reusable infrastructure components
- **Kubernetes**: Focus on resource management, scaling, security policies
- **Monitoring**: Implement comprehensive observability and alerting

### **File-Specific Context**
- **In `pulumi/`**: Focus on IaC best practices, resource management
- **In `k8s/`**: Focus on Kubernetes manifests, security, scaling
- **In `docker/`**: Focus on container optimization, security, health checks
- **In `monitoring/`**: Focus on metrics, alerts, dashboards

This IaC agent configuration ensures specialized assistance for infrastructure management while maintaining Orchestra AI's operational standards and security requirements. 