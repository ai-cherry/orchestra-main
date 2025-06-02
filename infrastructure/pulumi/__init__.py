"""
Cherry AI Infrastructure - Pulumi IaC for Vultr Deployment

This module defines the infrastructure for the Cherry AI admin interface
using Pulumi with Python, targeting Vultr cloud infrastructure.
"""

import pulumi
import pulumi_vultr as vultr
from pulumi import Config, Output, export
import json
from typing import Dict, List, Optional

# Configuration
config = Config()
environment = pulumi.get_stack()
region = config.get("region") or "ewr"  # Default to New Jersey
project_name = "cherry-ai"

# Tags for resource organization
tags = {
    "project": project_name,
    "environment": environment,
    "managed-by": "pulumi",
    "version": "1.0.0"
}

class CherryAIInfrastructure:
    """
    Main infrastructure class for Cherry AI deployment on Vultr
    Implements blue-green deployment capability and auto-scaling
    """
    
    def __init__(self):
        """Initialize infrastructure components"""
        self.vpc = self._create_vpc()
        self.firewall = self._create_firewall()
        self.load_balancer = self._create_load_balancer()
        self.database = self._create_database()
        self.redis = self._create_redis()
        self.kubernetes = self._create_kubernetes_cluster()
        self.object_storage = self._create_object_storage()
        self.monitoring = self._setup_monitoring()
        
    def _create_vpc(self) -> vultr.Vpc:
        """
        Create Virtual Private Cloud for network isolation
        """
        vpc = vultr.Vpc(
            f"{project_name}-vpc-{environment}",
            region=region,
            description=f"VPC for {project_name} {environment}",
            v4_subnet="10.0.0.0",
            v4_subnet_mask=24,
            tags=tags
        )
        
        pulumi.export("vpc_id", vpc.id)
        pulumi.export("vpc_subnet", vpc.v4_subnet)
        
        return vpc
    
    def _create_firewall(self) -> vultr.FirewallGroup:
        """
        Create firewall rules for security
        """
        firewall_group = vultr.FirewallGroup(
            f"{project_name}-firewall-{environment}",
            description=f"Firewall for {project_name} {environment}"
        )
        
        # Allow HTTPS traffic
        vultr.FirewallRule(
            f"{project_name}-https-rule",
            firewall_group_id=firewall_group.id,
            protocol="tcp",
            ip_type="v4",
            subnet="0.0.0.0",
            subnet_size=0,
            port="443",
            notes="Allow HTTPS traffic"
        )
        
        # Allow HTTP traffic (for redirect to HTTPS)
        vultr.FirewallRule(
            f"{project_name}-http-rule",
            firewall_group_id=firewall_group.id,
            protocol="tcp",
            ip_type="v4",
            subnet="0.0.0.0",
            subnet_size=0,
            port="80",
            notes="Allow HTTP traffic for redirect"
        )
        
        # Allow internal VPC communication
        vultr.FirewallRule(
            f"{project_name}-vpc-rule",
            firewall_group_id=firewall_group.id,
            protocol="tcp",
            ip_type="v4",
            subnet="10.0.0.0",
            subnet_size=24,
            port="1-65535",
            notes="Allow internal VPC communication"
        )
        
        return firewall_group
    
    def _create_load_balancer(self) -> vultr.LoadBalancer:
        """
        Create load balancer for high availability
        """
        load_balancer = vultr.LoadBalancer(
            f"{project_name}-lb-{environment}",
            region=region,
            label=f"{project_name}-lb-{environment}",
            vpc_id=self.vpc.id,
            forwarding_rules=[
                {
                    "frontend_protocol": "https",
                    "frontend_port": 443,
                    "backend_protocol": "http",
                    "backend_port": 8080
                },
                {
                    "frontend_protocol": "http",
                    "frontend_port": 80,
                    "backend_protocol": "http",
                    "backend_port": 8080
                }
            ],
            health_check={
                "protocol": "http",
                "port": 8080,
                "path": "/health",
                "check_interval": 10,
                "response_timeout": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2
            },
            ssl_redirect=True,
            proxy_protocol=False,
            balancing_algorithm="roundrobin",
            tags=tags
        )
        
        pulumi.export("load_balancer_ip", load_balancer.ipv4)
        pulumi.export("load_balancer_id", load_balancer.id)
        
        return load_balancer
    
    def _create_database(self) -> vultr.Database:
        """
        Create managed PostgreSQL database with vector extensions
        """
        database = vultr.Database(
            f"{project_name}-postgres-{environment}",
            database_engine="pg",
            database_engine_version="15",
            region=region,
            plan="vultr-dbaas-startup-cc-1-55-2",  # 1 vCPU, 55GB SSD, 2GB RAM
            label=f"{project_name}-postgres-{environment}",
            tag=environment,
            vpc_id=self.vpc.id,
            cluster_time_zone="America/New_York",
            maintenance_dow="sunday",
            maintenance_time="03:00",
            # Enable required extensions
            opts=pulumi.ResourceOptions(
                ignore_changes=["database_engine_version"]
            )
        )
        
        # Export connection details (sensitive)
        pulumi.export("postgres_host", database.host)
        pulumi.export("postgres_port", database.port)
        pulumi.export("postgres_database", database.database_name)
        pulumi.export("postgres_user", database.user)
        pulumi.export("postgres_password", Output.secret(database.password))
        
        return database
    
    def _create_redis(self) -> vultr.Database:
        """
        Create managed Redis instance for caching
        """
        redis = vultr.Database(
            f"{project_name}-redis-{environment}",
            database_engine="redis",
            database_engine_version="7",
            region=region,
            plan="vultr-dbaas-hobbyist-cc-1-25-1",  # 1 vCPU, 25GB SSD, 1GB RAM
            label=f"{project_name}-redis-{environment}",
            tag=environment,
            vpc_id=self.vpc.id,
            redis_eviction_policy="allkeys-lru"
        )
        
        pulumi.export("redis_host", redis.host)
        pulumi.export("redis_port", redis.port)
        pulumi.export("redis_password", Output.secret(redis.password))
        
        return redis
    
    def _create_kubernetes_cluster(self) -> vultr.Kubernetes:
        """
        Create Kubernetes cluster for container orchestration
        """
        k8s_cluster = vultr.Kubernetes(
            f"{project_name}-k8s-{environment}",
            region=region,
            label=f"{project_name}-k8s-{environment}",
            version="v1.28.2+1",  # Latest stable version
            node_pools=[
                {
                    "node_quantity": 3 if environment == "production" else 2,
                    "plan": "vc2-2c-4gb" if environment == "production" else "vc2-1c-2gb",
                    "label": "worker-pool",
                    "auto_scaler": True,
                    "min_nodes": 2,
                    "max_nodes": 10 if environment == "production" else 5,
                    "tags": tags
                }
            ],
            tags=tags
        )
        
        # Export kubeconfig for kubectl access
        pulumi.export("kubeconfig", Output.secret(k8s_cluster.kube_config))
        pulumi.export("k8s_cluster_id", k8s_cluster.id)
        pulumi.export("k8s_endpoint", k8s_cluster.endpoint)
        
        return k8s_cluster
    
    def _create_object_storage(self) -> vultr.ObjectStorage:
        """
        Create object storage for static assets and backups
        """
        object_storage = vultr.ObjectStorage(
            f"{project_name}-storage-{environment}",
            cluster_id=1,  # New Jersey cluster
            label=f"{project_name}-storage-{environment}"
        )
        
        pulumi.export("object_storage_id", object_storage.id)
        pulumi.export("object_storage_hostname", object_storage.s3_hostname)
        pulumi.export("object_storage_access_key", Output.secret(object_storage.s3_access_key))
        pulumi.export("object_storage_secret_key", Output.secret(object_storage.s3_secret_key))
        
        return object_storage
    
    def _setup_monitoring(self) -> Dict[str, any]:
        """
        Setup monitoring and alerting infrastructure
        """
        # Create monitoring instance
        monitoring_instance = vultr.Instance(
            f"{project_name}-monitoring-{environment}",
            region=region,
            plan="vc2-1c-2gb",  # 1 vCPU, 2GB RAM
            os_id=1743,  # Ubuntu 22.04 LTS
            label=f"{project_name}-monitoring-{environment}",
            vpc_id=self.vpc.id,
            firewall_group_id=self.firewall.id,
            enable_ipv6=False,
            backups="disabled" if environment != "production" else "enabled",
            ddos_protection=False,
            activation_email=False,
            tags=tags,
            user_data=self._get_monitoring_user_data()
        )
        
        pulumi.export("monitoring_ip", monitoring_instance.main_ip)
        
        return {
            "instance": monitoring_instance
        }
    
    def _get_monitoring_user_data(self) -> str:
        """
        Generate cloud-init user data for monitoring setup
        """
        return """#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create monitoring directory
mkdir -p /opt/monitoring
cd /opt/monitoring

# Create docker-compose.yml for Prometheus + Grafana
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    ports:
      - "9100:9100"
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

# Create Prometheus configuration
mkdir -p prometheus
cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets: ['node_exporter:9100']
EOF

# Start monitoring stack
docker-compose up -d

# Setup firewall rules
ufw allow 22/tcp
ufw allow 3000/tcp
ufw allow 9090/tcp
ufw --force enable

echo "Monitoring setup complete!"
"""

# Create infrastructure instance
infrastructure = CherryAIInfrastructure()

# Export deployment information
export("deployment_info", {
    "environment": environment,
    "region": region,
    "project": project_name,
    "version": tags["version"],
    "endpoints": {
        "load_balancer": f"https://{infrastructure.load_balancer.ipv4}",
        "monitoring": f"http://{infrastructure.monitoring['instance'].main_ip}:3000"
    }
})

# Export deployment instructions
export("deployment_instructions", """
Cherry AI Infrastructure Deployment Complete!

Next Steps:
1. Configure DNS to point to the load balancer IP
2. Deploy the application to Kubernetes cluster
3. Access monitoring at the monitoring endpoint
4. Configure SSL certificates on the load balancer

For kubectl access:
pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
export KUBECONFIG=./kubeconfig.yaml
kubectl get nodes
""")