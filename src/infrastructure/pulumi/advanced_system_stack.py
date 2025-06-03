# TODO: Consider adding connection pooling configuration
"""
"""
project_name = "orchestra-advanced"
environment = config.get("environment") or "production"

# Tags for all resources
common_tags = {
    "project": project_name,
    "environment": environment,
    "managed_by": "pulumi"
}

# Network Configuration
vpc = vultr.Vpc(f"{project_name}-vpc",
    region="ewr",  # New Jersey for low latency
    description=f"VPC for {project_name} {environment}",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=16,  # Allows for 65k hosts
    tags=common_tags
)

# Kubernetes Cluster for Microservices
k8s_cluster = vultr.Kubernetes(f"{project_name}-k8s",
    region="ewr",
    version="v1.28.2+1",
    label=f"{project_name}-cluster",
    node_pools=[
        {
            "node_quantity": 3,
            "plan": "vc2-4c-8gb",  # 4 vCPU, 8GB RAM per node
            "label": "search-pool",
            "auto_scaler": True,
            "min_nodes": 3,
            "max_nodes": 10,
            "tags": {**common_tags, "pool": "search"}
        },
        {
            "node_quantity": 2,
            "plan": "vc2-2c-4gb",  # 2 vCPU, 4GB RAM per node
            "label": "ingestion-pool",
            "auto_scaler": True,
            "min_nodes": 2,
            "max_nodes": 5,
            "tags": {**common_tags, "pool": "ingestion"}
        },
        {
            "node_quantity": 2,
            "plan": "vc2-4c-8gb",  # For ML workloads
            "label": "ml-pool",
            "auto_scaler": True,
            "min_nodes": 1,
            "max_nodes": 4,
            "tags": {**common_tags, "pool": "ml"}
        }
    ],
    tags=common_tags
)

# PostgreSQL Database Cluster
postgres_cluster = vultr.Database(f"{project_name}-postgres",
    database_engine="pg",
    database_engine_version="15",
    region="ewr",
    plan="vultr-dbaas-hobbyist-cc-1-25-1",  # 1 vCPU, 1GB RAM, 25GB storage
    label=f"{project_name}-db",
    cluster_time_zone="America/New_York",
    maintenance_dow="sunday",
    maintenance_time="03:00",
    trusted_ips=["10.0.0.0/16"],  # Only VPC access
    tags=common_tags
)

# Redis Cluster for Caching and Queues
redis_instances = []
for i, purpose in enumerate(["cache", "queue", "session"]):
    redis = vultr.Instance(f"{project_name}-redis-{purpose}",
        region="ewr",
        plan="vc2-1c-2gb",
        os_id=1743,  # Ubuntu 22.04
        label=f"{project_name}-redis-{purpose}",
        vpc_ids=[vpc.id],
        tags={**common_tags, "component": "redis", "purpose": purpose},
        user_data=f"""
echo "requirepass {config.require_secret('redis_password')}" >> /etc/redis/redis.conf
systemctl restart redis-server
"""
for domain in ["search", "personas", "knowledge"]:
    weaviate = vultr.Instance(f"{project_name}-weaviate-{domain}",
        region="ewr",
        plan="vc2-2c-4gb",  # 2 vCPU, 4GB RAM
        os_id=1743,  # Ubuntu 22.04
        label=f"{project_name}-weaviate-{domain}",
        vpc_ids=[vpc.id],
        tags={**common_tags, "component": "weaviate", "domain": domain},
        user_data=f"""
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-openai'
      ENABLE_MODULES: 'text2vec-openai,generative-openai'
      CLUSTER_HOSTNAME: 'weaviate-{domain}'
    volumes:
      - /var/lib/weaviate:/var/lib/weaviate
EOF
cd /opt/weaviate && docker-compose up -d
"""
load_balancer = vultr.LoadBalancer(f"{project_name}-lb",
    region="ewr",
    label=f"{project_name}-api-gateway",
    vpc_id=vpc.id,
    forwarding_rules=[
        {
            "frontend_protocol": "https",
            "frontend_port": 443,
            "backend_protocol": "http",
            "backend_port": 80,
            "target_port": 8000
        },
        {
            "frontend_protocol": "http",
            "frontend_port": 80,
            "backend_protocol": "http",
            "backend_port": 80,
            "target_port": 8000
        }
    ],
    health_check={
        "protocol": "http",
        "port": 8000,
        "path": "/health",
        "check_interval": 10,
        "response_timeout": 5,
        "unhealthy_threshold": 3,
        "healthy_threshold": 2
    },
    ssl_redirect=True,
    tags=common_tags
)

# Object Storage for Multimedia
object_storage = vultr.ObjectStorage(f"{project_name}-storage",
    cluster_id=1,  # New Jersey cluster
    label=f"{project_name}-multimedia",
    tags=common_tags
)

# Create storage buckets
buckets = {}
for bucket_name in ["images", "videos", "documents", "models"]:
    bucket = vultr.ObjectStorageBucket(f"{project_name}-{bucket_name}",
        object_storage_cluster_id=object_storage.id,
        label=f"{project_name}-{bucket_name}",
        tags={**common_tags, "bucket": bucket_name}
    )
    buckets[bucket_name] = bucket

# Firewall Rules
firewall = vultr.Firewall(f"{project_name}-firewall",
    description=f"Firewall for {project_name}",
    rules=[
        # Allow internal VPC traffic
        {
            "ip_type": "v4",
            "protocol": "tcp",
            "subnet": "10.0.0.0",
            "subnet_size": 16,
            "port": "1-65535",
            "notes": "Allow all internal VPC traffic"
        },
        # Allow HTTPS
        {
            "ip_type": "v4",
            "protocol": "tcp",
            "subnet": "0.0.0.0",
            "subnet_size": 0,
            "port": "443",
            "notes": "Allow HTTPS"
        },
        # Allow HTTP (will redirect to HTTPS)
        {
            "ip_type": "v4",
            "protocol": "tcp",
            "subnet": "0.0.0.0",
            "subnet_size": 0,
            "port": "80",
            "notes": "Allow HTTP"
        },
        # Allow SSH from specific IPs only
        {
            "ip_type": "v4",
            "protocol": "tcp",
            "subnet": config.get("admin_ip") or "0.0.0.0",
            "subnet_size": 32,
            "port": "22",
            "notes": "SSH access"
        }
    ],
    tags=common_tags
)

# Monitoring Instance
monitoring = vultr.Instance(f"{project_name}-monitoring",
    region="ewr",
    plan="vc2-2c-4gb",
    os_id=1743,  # Ubuntu 22.04
    label=f"{project_name}-monitoring",
    vpc_ids=[vpc.id],
    firewall_group_id=firewall.id,
    tags={**common_tags, "component": "monitoring"},
    user_data="""
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
  
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
EOF

cd /opt/monitoring && docker-compose up -d
"""
pulumi.export("vpc_id", vpc.id)
pulumi.export("k8s_cluster_id", k8s_cluster.id)
pulumi.export("k8s_config", k8s_cluster.kube_config)
pulumi.export("postgres_connection", postgres_cluster.connection_uri)
pulumi.export("redis_endpoints", {
    "cache": redis_instances[0].main_ip,
    "queue": redis_instances[1].main_ip,
    "session": redis_instances[2].main_ip
})
pulumi.export("weaviate_endpoints", {
    "search": f"http://{weaviate_instances[0].main_ip}:8080",
    "personas": f"http://{weaviate_instances[1].main_ip}:8080",
    "knowledge": f"http://{weaviate_instances[2].main_ip}:8080"
})
pulumi.export("load_balancer_ip", load_balancer.ipv4)
pulumi.export("object_storage_endpoint", object_storage.s3_hostname)
pulumi.export("monitoring_endpoint", f"http://{monitoring.main_ip}:3000")

# Configuration for hot-swapping
module_config = {
    "search_engine": {
        "endpoint": f"http://{load_balancer.ipv4}/api/search",
        "weaviate": f"http://{weaviate_instances[0].main_ip}:8080",
        "cache": f"redis://{redis_instances[0].main_ip}:6379"
    },
    "file_ingestion": {
        "endpoint": f"http://{load_balancer.ipv4}/api/ingest",
        "storage": object_storage.s3_hostname,
        "queue": f"redis://{redis_instances[1].main_ip}:6379"
    },
    "multimedia": {
        "endpoint": f"http://{load_balancer.ipv4}/api/multimedia",
        "storage": {
            "images": f"s3://{buckets['images'].label}",
            "videos": f"s3://{buckets['videos'].label}"
        }
    },
    "personas": {
        "weaviate": f"http://{weaviate_instances[1].main_ip}:8080",
        "postgres": postgres_cluster.connection_uri
    }
}

pulumi.export("module_configuration", module_config)