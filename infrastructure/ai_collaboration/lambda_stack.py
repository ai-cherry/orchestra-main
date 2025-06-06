#!/usr/bin/env python3
"""
Pulumi Infrastructure Stack for AI Collaboration Dashboard on Lambda
Production-ready infrastructure with monitoring, scaling, and resilience
"""

import pulumi
import pulumi_lambda as Lambda
from pulumi import Config, Output, ResourceOptions, export
from typing import Dict, Any, List
import json


class AICollaborationStack:
    """
    Complete infrastructure stack for AI Collaboration Dashboard
    Implements blue-green deployment, auto-scaling, and monitoring
    """
    
    def __init__(self):
        self.config = Config()
        self.stack = pulumi.get_stack()
        self.project = pulumi.get_project()
        
        # Configuration
        self.region = self.config.get("region") or "ewr"  # New Jersey
        self.environment = self.stack
        self.domain = self.config.require("domain")  # cherry-ai.me
        
        # Resource naming
        self.name_prefix = f"{self.project}-{self.environment}"
        
        # Create all infrastructure
        self._create_network()
        self._create_redis_cluster()
        self._create_postgres_replica()
        self._create_application_instances()
        self._create_load_balancer()
        self._create_monitoring()
        self._create_cdn()
        self._create_dns()
        self._export_outputs()
    
    def _create_network(self):
        """Create VPC and networking infrastructure"""
        # Create VPC for isolation
        self.vpc = lambda.Vpc(
            f"{self.name_prefix}-vpc",
            region=self.region,
            description="AI Collaboration VPC",
            v4_subnet="10.0.0.0",
            v4_subnet_mask=16
        )
        
        # Create firewall group
        self.firewall_group = lambda.FirewallGroup(
            f"{self.name_prefix}-firewall",
            description="AI Collaboration Firewall Rules"
        )
        
        # Firewall rules
        firewall_rules = [
            # Allow internal VPC traffic
            {"protocol": "tcp", "subnet": "10.0.0.0", "subnet_size": 16, "port": "1-65535", "source": "10.0.0.0/16"},
            # Allow HTTP/HTTPS from anywhere
            {"protocol": "tcp", "subnet": "0.0.0.0", "subnet_size": 0, "port": "80"},
            {"protocol": "tcp", "subnet": "0.0.0.0", "subnet_size": 0, "port": "443"},
            # Allow WebSocket
            {"protocol": "tcp", "subnet": "0.0.0.0", "subnet_size": 0, "port": "8765"},
            # Allow SSH from specific IPs (configure as needed)
            {"protocol": "tcp", "subnet": self.config.get("admin_ip") or "0.0.0.0", "subnet_size": 32, "port": "22"},
        ]
        
        for i, rule in enumerate(firewall_rules):
            lambda.FirewallRule(
                f"{self.name_prefix}-fw-rule-{i}",
                firewall_group_id=self.firewall_group.id,
                protocol=rule["protocol"],
                subnet=rule["subnet"],
                subnet_size=rule["subnet_size"],
                port=rule.get("port", ""),
                source=rule.get("source", "")
            )
    
    def _create_redis_cluster(self):
        """Create Redis cluster for real-time data"""
        # Redis instances for high availability
        self.redis_instances = []
        
        for i in range(3):  # 3-node cluster
            instance = lambda.Instance(
                f"{self.name_prefix}-redis-{i}",
                plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
                region=self.region,
                os_id=387,  # Ubuntu 22.04
                vpc_ids=[self.vpc.id],
                firewall_group_id=self.firewall_group.id,
                label=f"Redis Node {i}",
                tag=f"{self.environment}-redis",
                backups="enabled",
                ddos_protection=True,
                activation_email=False,
                user_data=self._get_redis_user_data(i)
            )
            self.redis_instances.append(instance)
        
        # Create Redis load balancer
        self.redis_lb = lambda.LoadBalancer(
            f"{self.name_prefix}-redis-lb",
            region=self.region,
            vpc_id=self.vpc.id,
            label="Redis Load Balancer",
            balancing_algorithm="roundrobin",
            health_check={
                "protocol": "tcp",
                "port": 6379,
                "check_interval": 10,
                "response_timeout": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2
            },
            forwarding_rules=[{
                "frontend_protocol": "tcp",
                "frontend_port": 6379,
                "backend_protocol": "tcp",
                "backend_port": 6379
            }],
            instances=[instance.id for instance in self.redis_instances]
        )
    
    def _create_postgres_replica(self):
        """Create PostgreSQL read replica for analytics"""
        # PostgreSQL read replica
        self.postgres_replica = lambda.Database(
            f"{self.name_prefix}-postgres-replica",
            database_engine="pg",
            database_engine_version="14",
            region=self.region,
            plan="Lambda-dbaas-startup-cc-1-25-2",  # 1 vCPU, 2GB RAM, 25GB storage
            label="PostgreSQL Read Replica",
            tag=f"{self.environment}-postgres",
            vpc_id=self.vpc.id,
            maintenance_dow="sunday",
            maintenance_time="03:00",
            mysql_sql_modes=[],  # Not used for PostgreSQL
            mysql_require_primary_key=False,  # Not used for PostgreSQL
            redis_eviction_policy="",  # Not used for PostgreSQL
            read_replicas=1
        )
    
    def _create_application_instances(self):
        """Create application instances with auto-scaling"""
        # Base instance configuration
        self.app_instances = []
        
        # Create instances for blue-green deployment
        for color in ["blue", "green"]:
            for i in range(2):  # Start with 2 instances per color
                instance = lambda.Instance(
                    f"{self.name_prefix}-app-{color}-{i}",
                    plan="vc2-4c-8gb",  # 4 vCPU, 8GB RAM
                    region=self.region,
                    os_id=387,  # Ubuntu 22.04
                    vpc_ids=[self.vpc.id],
                    firewall_group_id=self.firewall_group.id,
                    label=f"App Instance {color}-{i}",
                    tag=f"{self.environment}-app-{color}",
                    backups="enabled",
                    ddos_protection=True,
                    activation_email=False,
                    user_data=self._get_app_user_data(color)
                )
                self.app_instances.append(instance)
        
        # Create snapshot for auto-scaling
        self.app_snapshot = lambda.Snapshot(
            f"{self.name_prefix}-app-snapshot",
            instance_id=self.app_instances[0].id,
            description="AI Collaboration App Snapshot"
        )
    
    def _create_load_balancer(self):
        """Create application load balancer with health checks"""
        # Get active instances (blue or green based on deployment)
        active_color = self.config.get("active_deployment") or "blue"
        active_instances = [
            instance for instance in self.app_instances
            if f"-{active_color}-" in instance._name
        ]
        
        self.app_lb = lambda.LoadBalancer(
            f"{self.name_prefix}-app-lb",
            region=self.region,
            vpc_id=self.vpc.id,
            label="Application Load Balancer",
            balancing_algorithm="leastconn",
            ssl_redirect=True,
            proxy_protocol=True,
            health_check={
                "protocol": "http",
                "port": 8000,
                "path": "/health",
                "check_interval": 10,
                "response_timeout": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2
            },
            forwarding_rules=[
                {
                    "frontend_protocol": "http",
                    "frontend_port": 80,
                    "backend_protocol": "http",
                    "backend_port": 8000
                },
                {
                    "frontend_protocol": "https",
                    "frontend_port": 443,
                    "backend_protocol": "http",
                    "backend_port": 8000
                },
                {
                    "frontend_protocol": "tcp",
                    "frontend_port": 8765,
                    "backend_protocol": "tcp",
                    "backend_port": 8765
                }
            ],
            instances=[instance.id for instance in active_instances],
            ssl={
                "private_key": self.config.require_secret("ssl_private_key"),
                "certificate": self.config.require_secret("ssl_certificate"),
                "chain": self.config.get_secret("ssl_chain")
            }
        )
    
    def _create_monitoring(self):
        """Create monitoring and alerting infrastructure"""
        # Monitoring instance
        self.monitoring = lambda.Instance(
            f"{self.name_prefix}-monitoring",
            plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
            region=self.region,
            os_id=387,  # Ubuntu 22.04
            vpc_ids=[self.vpc.id],
            firewall_group_id=self.firewall_group.id,
            label="Monitoring Instance",
            tag=f"{self.environment}-monitoring",
            backups="enabled",
            activation_email=False,
            user_data=self._get_monitoring_user_data()
        )
        
        # Create alerts (using Lambda's alert system)
        # Note: In production, integrate with external monitoring like Datadog
    
    def _create_cdn(self):
        """Create CDN configuration for static assets"""
        # Lambda doesn't have native CDN, so we'll use object storage with CDN
        self.object_storage = lambda.ObjectStorage(
            f"{self.name_prefix}-cdn",
            cluster_id=self.config.get("object_storage_cluster") or 1,
            label="AI Collaboration CDN Storage"
        )
    
    def _create_dns(self):
        """Create DNS records"""
        # Create DNS domain if not exists
        self.domain_record = lambda.DnsDomain(
            f"{self.name_prefix}-domain",
            domain=self.domain,
            ip=self.app_lb.ipv4
        )
        
        # DNS records
        dns_records = [
            {"name": "@", "type": "A", "data": self.app_lb.ipv4},
            {"name": "www", "type": "CNAME", "data": f"{self.domain}."},
            {"name": "api", "type": "A", "data": self.app_lb.ipv4},
            {"name": "ws", "type": "A", "data": self.app_lb.ipv4},
            {"name": "cdn", "type": "CNAME", "data": self.object_storage.s3_hostname}
        ]
        
        for record in dns_records:
            lambda.DnsRecord(
                f"{self.name_prefix}-dns-{record['name']}-{record['type']}",
                domain=self.domain,
                name=record["name"],
                type=record["type"],
                data=record["data"],
                ttl=300
            )
    
    def _get_redis_user_data(self, node_index: int) -> str:
        """Generate Redis node initialization script"""
        return f"""#!/bin/bash
# Redis Node {node_index} Setup
apt-get update
apt-get install -y redis-server redis-sentinel

# Configure Redis
cat > /etc/redis/redis.conf << EOF
bind 0.0.0.0
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
replica-priority 100
maxmemory 3gb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 15000
EOF

# Start Redis
systemctl restart redis-server
systemctl enable redis-server

# Configure monitoring
apt-get install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
"""
    
    def _get_app_user_data(self, color: str) -> str:
        """Generate application instance initialization script"""
        return f"""#!/bin/bash
# Application Instance Setup - {color}
apt-get update
apt-get install -y docker.io docker-compose git nginx certbot python3-certbot-nginx

# Clone application
git clone https://github.com/your-repo/orchestra-main-2.git /opt/app
cd /opt/app

# Set environment
cat > .env << EOF
ENVIRONMENT={self.environment}
DEPLOYMENT_COLOR={color}
DATABASE_URL=postgresql://user:pass@{self.postgres_replica.host}:{self.postgres_replica.port}/db
REDIS_URL=redis://{self.redis_lb.ipv4}:6379
WEAVIATE_URL=http://weaviate:8080
API_URL=https://api.{self.domain}
WEBSOCKET_URL=wss://ws.{self.domain}:8765
EOF

# Start services
docker-compose up -d

# Configure Nginx
cat > /etc/nginx/sites-available/app << EOF
server {{
    listen 80;
    server_name {self.domain} www.{self.domain};
    
    location / {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }}
    
    location /ws {{
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }}
}}
EOF

ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
systemctl restart nginx

# Configure monitoring
apt-get install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Auto-scaling agent
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
EOF
chmod +x /usr/local/bin/health-check.sh
"""
    
    def _get_monitoring_user_data(self) -> str:
        """Generate monitoring instance initialization script"""
        return """#!/bin/bash
# Monitoring Setup
apt-get update
apt-get install -y prometheus grafana telegraf

# Configure Prometheus
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['10.0.0.0/16:9100']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['10.0.0.0/16:9121']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['10.0.0.0/16:9187']
  
  - job_name: 'app'
    static_configs:
      - targets: ['10.0.0.0/16:8000']
EOF

# Start services
systemctl restart prometheus
systemctl enable prometheus
systemctl restart grafana-server
systemctl enable grafana-server

# Configure alerts
cat > /etc/prometheus/alerts.yml << EOF
groups:
  - name: ai_collaboration
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
      
      - alert: HighMemoryUsage
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High memory usage detected
EOF
"""
    
    def _export_outputs(self):
        """Export stack outputs"""
        export("vpc_id", self.vpc.id)
        export("app_lb_ip", self.app_lb.ipv4)
        export("app_lb_hostname", self.app_lb.hostname)
        export("redis_lb_ip", self.redis_lb.ipv4)
        export("postgres_host", self.postgres_replica.host)
        export("postgres_port", self.postgres_replica.port)
        export("object_storage_endpoint", self.object_storage.s3_hostname)
        export("monitoring_ip", self.monitoring.main_ip)
        export("domain", self.domain)
        export("active_deployment", self.config.get("active_deployment") or "blue")
        
        # Instance IPs for direct access
        export("app_instance_ips", [instance.main_ip for instance in self.app_instances])
        export("redis_instance_ips", [instance.main_ip for instance in self.redis_instances])
        
        # Cost estimation
        export("estimated_monthly_cost", self._calculate_monthly_cost())
    
    def _calculate_monthly_cost(self) -> str:
        """Calculate estimated monthly cost"""
        costs = {
            "app_instances": len(self.app_instances) * 48,  # $48/month for vc2-4c-8gb
            "redis_instances": len(self.redis_instances) * 24,  # $24/month for vc2-2c-4gb
            "postgres_replica": 15,  # $15/month for startup plan
            "load_balancers": 2 * 10,  # $10/month per LB
            "monitoring": 24,  # $24/month for vc2-2c-4gb
            "object_storage": 5,  # $5/month base
            "bandwidth": 50,  # Estimated bandwidth costs
        }
        
        total = sum(costs.values())
        return f"${total}/month (breakdown: {json.dumps(costs, indent=2)})"


# Create the stack
def create_stack():
    """Create the AI Collaboration infrastructure stack"""
    return AICollaborationStack()


# Pulumi program
stack = create_stack()