#!/usr/bin/env python3
"""
Pulumi Infrastructure as Code for AI Collaboration Dashboard
Targets Vultr provider with modular, hot-swappable components
"""

import pulumi
import pulumi_vultr as vultr
from pulumi import Config, Output, export
import json

# Configuration
config = Config()
project_name = "ai-collaboration"
environment = config.get("environment") or "production"

# Vultr configuration
vultr_config = {
    "region": "ewr",  # New Jersey datacenter for low latency
    "plan": "vc2-4c-8gb",  # 4 vCPU, 8GB RAM for services
    "os_id": 387,  # Ubuntu 22.04 LTS
}

class AICollaborationInfrastructure:
    """
    Modular infrastructure components for AI Collaboration Dashboard
    Following performance-first design principles
    """
    
    def __init__(self):
        self.vpc = self._create_vpc()
        self.redis_cluster = self._create_redis_cluster()
        self.postgres_replica = self._create_postgres_replica()
        self.load_balancer = self._create_load_balancer()
        self.cdn = self._create_cdn()
        self.monitoring = self._create_monitoring()
        
    def _create_vpc(self):
        """Create isolated VPC for AI collaboration services"""
        vpc = vultr.Vpc(
            f"{project_name}-vpc",
            region=vultr_config["region"],
            description="AI Collaboration Services VPC",
            v4_subnet="10.10.0.0",
            v4_subnet_mask=24
        )
        
        # Security group for internal services
        security_group = vultr.FirewallGroup(
            f"{project_name}-internal-sg",
            description="Internal services security group"
        )
        
        # Allow internal communication
        vultr.FirewallRule(
            f"{project_name}-internal-rule",
            firewall_group_id=security_group.id,
            protocol="tcp",
            ip_type="v4",
            subnet="10.10.0.0",
            subnet_size=24,
            port="1-65535"
        )
        
        return vpc
        
    def _create_redis_cluster(self):
        """Create Redis cluster for real-time AI collaboration data"""
        # Master node
        redis_master = vultr.Instance(
            f"{project_name}-redis-master",
            plan=vultr_config["plan"],
            region=vultr_config["region"],
            os_id=vultr_config["os_id"],
            vpc_ids=[self.vpc.id],
            label="AI Collaboration Redis Master",
            tag="ai-collaboration",
            user_data=self._get_redis_master_userdata(),
            backups="enabled",
            ddos_protection=True
        )
        
        # Replica nodes for high availability
        redis_replicas = []
        for i in range(2):
            replica = vultr.Instance(
                f"{project_name}-redis-replica-{i}",
                plan="vc2-2c-4gb",  # Smaller instances for replicas
                region=vultr_config["region"],
                os_id=vultr_config["os_id"],
                vpc_ids=[self.vpc.id],
                label=f"AI Collaboration Redis Replica {i}",
                tag="ai-collaboration",
                user_data=self._get_redis_replica_userdata(redis_master),
                backups="enabled"
            )
            redis_replicas.append(replica)
            
        return {
            "master": redis_master,
            "replicas": redis_replicas
        }
        
    def _create_postgres_replica(self):
        """Create PostgreSQL read replica for analytics queries"""
        # Using Vultr Database service for managed PostgreSQL
        postgres_replica = vultr.Database(
            f"{project_name}-postgres-replica",
            database_engine="pg",
            database_engine_version="14",
            region=vultr_config["region"],
            plan="vultr-dbaas-startup-cc-1-55-2",
            label="AI Collaboration Analytics DB",
            tag="ai-collaboration",
            cluster_time_zone="America/New_York",
            maintenance_dow="sunday",
            maintenance_time="03:00",
            read_replicas=1,  # Enable read replica
            trusted_ips=["10.10.0.0/24"]  # Only VPC access
        )
        
        return postgres_replica
        
    def _create_load_balancer(self):
        """Create load balancer for WebSocket connections"""
        # Health check configuration
        health_check = {
            "protocol": "http",
            "port": 8000,
            "path": "/health",
            "check_interval": 5,
            "response_timeout": 3,
            "unhealthy_threshold": 2,
            "healthy_threshold": 2
        }
        
        # Load balancer for WebSocket and API traffic
        lb = vultr.LoadBalancer(
            f"{project_name}-lb",
            region=vultr_config["region"],
            label="AI Collaboration Load Balancer",
            balancing_algorithm="roundrobin",
            health_check=health_check,
            forwarding_rules=[
                {
                    "frontend_protocol": "http",
                    "frontend_port": 80,
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
            ssl_redirect=True,
            proxy_protocol=True,
            sticky_sessions={
                "cookie_name": "ai_collab_session",
                "cookie_ttl_seconds": 3600
            }
        )
        
        return lb
        
    def _create_cdn(self):
        """Create CDN configuration for dashboard assets"""
        # Vultr doesn't have native CDN, so we'll use a dedicated instance
        # with nginx and caching configured
        cdn_instance = vultr.Instance(
            f"{project_name}-cdn",
            plan="vc2-1c-2gb",  # Small instance for static assets
            region=vultr_config["region"],
            os_id=vultr_config["os_id"],
            label="AI Collaboration CDN",
            tag="ai-collaboration",
            user_data=self._get_cdn_userdata(),
            backups="enabled",
            ddos_protection=True
        )
        
        # Reserved IP for CDN
        cdn_ip = vultr.ReservedIp(
            f"{project_name}-cdn-ip",
            region=vultr_config["region"],
            ip_type="v4",
            label="AI Collaboration CDN IP",
            instance_id=cdn_instance.id
        )
        
        return {
            "instance": cdn_instance,
            "ip": cdn_ip
        }
        
    def _create_monitoring(self):
        """Create monitoring infrastructure"""
        monitoring_instance = vultr.Instance(
            f"{project_name}-monitoring",
            plan="vc2-2c-4gb",
            region=vultr_config["region"],
            os_id=vultr_config["os_id"],
            vpc_ids=[self.vpc.id],
            label="AI Collaboration Monitoring",
            tag="ai-collaboration",
            user_data=self._get_monitoring_userdata(),
            backups="enabled"
        )
        
        return monitoring_instance
        
    def _get_redis_master_userdata(self):
        """User data script for Redis master setup"""
        return """#!/bin/bash
# Redis Master Setup for AI Collaboration
apt-get update
apt-get install -y redis-server python3-pip

# Configure Redis for performance
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
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
replica-priority 100
maxmemory 4gb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

# Performance tuning
echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p

# Disable THP
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo "echo never > /sys/kernel/mm/transparent_hugepage/enabled" >> /etc/rc.local

# Start Redis
systemctl restart redis-server
systemctl enable redis-server

# Install monitoring
pip3 install redis prometheus-client
"""
        
    def _get_redis_replica_userdata(self, master):
        """User data script for Redis replica setup"""
        return f"""#!/bin/bash
# Redis Replica Setup
apt-get update
apt-get install -y redis-server

# Configure as replica
echo "replicaof {master.internal_ip} 6379" >> /etc/redis/redis.conf

# Start Redis
systemctl restart redis-server
systemctl enable redis-server
"""
        
    def _get_cdn_userdata(self):
        """User data script for CDN setup"""
        return """#!/bin/bash
# CDN Setup with Nginx
apt-get update
apt-get install -y nginx

# Configure Nginx for caching
cat > /etc/nginx/sites-available/cdn << EOF
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=ai_cache:100m max_size=10g inactive=60m use_temp_path=off;

server {
    listen 80;
    server_name _;
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://backend;
        proxy_cache ai_cache;
        proxy_cache_valid 200 302 60m;
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_background_update on;
        proxy_cache_lock on;
        
        add_header X-Cache-Status $upstream_cache_status;
        add_header Cache-Control "public, max-age=31536000, immutable";
        
        # Compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/css application/javascript application/json image/svg+xml;
    }
}
EOF

ln -s /etc/nginx/sites-available/cdn /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Performance tuning
cat >> /etc/nginx/nginx.conf << EOF
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 65535;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
EOF

systemctl restart nginx
systemctl enable nginx
"""
        
    def _get_monitoring_userdata(self):
        """User data script for monitoring setup"""
        return """#!/bin/bash
# Monitoring Setup with Prometheus and Grafana
apt-get update
apt-get install -y prometheus grafana

# Configure Prometheus for AI metrics
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-collaboration'
    static_configs:
      - targets: ['localhost:9090']
        
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-master:9121']
        
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
        
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
EOF

# Start services
systemctl restart prometheus
systemctl enable prometheus
systemctl restart grafana-server
systemctl enable grafana-server

# Install exporters
apt-get install -y prometheus-node-exporter prometheus-redis-exporter
"""

# Create infrastructure
infra = AICollaborationInfrastructure()

# Exports for use in application configuration
export("redis_master_ip", infra.redis_cluster["master"].main_ip)
export("redis_master_internal_ip", infra.redis_cluster["master"].internal_ip)
export("postgres_replica_host", infra.postgres_replica.host)
export("postgres_replica_port", infra.postgres_replica.port)
export("load_balancer_ip", infra.load_balancer.ipv4)
export("cdn_ip", infra.cdn["ip"].ip)
export("monitoring_ip", infra.monitoring.main_ip)

# Output configuration for application
export("ai_collaboration_config", Output.all(
    redis_master=infra.redis_cluster["master"].internal_ip,
    postgres_host=infra.postgres_replica.host,
    postgres_port=infra.postgres_replica.port,
    load_balancer=infra.load_balancer.ipv4,
    cdn_endpoint=infra.cdn["ip"].ip
).apply(lambda args: json.dumps({
    "redis": {
        "host": args["redis_master"],
        "port": 6379
    },
    "postgres": {
        "host": args["postgres_host"],
        "port": args["postgres_port"],
        "database": "ai_collaboration"
    },
    "endpoints": {
        "api": f"http://{args['load_balancer']}",
        "websocket": f"ws://{args['load_balancer']}:8765",
        "cdn": f"http://{args['cdn_endpoint']}"
    }
}, indent=2)))