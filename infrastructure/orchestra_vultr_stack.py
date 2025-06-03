# TODO: Consider adding connection pooling configuration
"""
"""
vpc = vultr.Vpc("orchestra-vpc",
    region="ewr",
    description="Orchestra AI VPC",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create Kubernetes cluster
k8s_cluster = vultr.Kubernetes("orchestra-k8s",
    region="ewr",
    version="v1.28.2+1",
    node_pools=[{
        "node_quantity": 3,
        "plan": "vc2-2c-4gb",
        "label": "orchestra-workers",
        "auto_scaler": True,
        "min_nodes": 3,
        "max_nodes": 10
    }]
)

# Create managed PostgreSQL
postgres = vultr.Database("orchestra-postgres",
    database_engine="pg",
    database_engine_version="15",
    region="ewr",
    plan="vultr-dbaas-startup-cc-1-55-2",
    label="orchestra-db",
    tag="production",
    cluster_time_zone="America/New_York",
    maintenance_dow="sunday",
    maintenance_time="03:00",
    trusted_ips=["10.0.0.0/24"]
)

# Create Redis instance
redis = vultr.Instance("orchestra-redis",
    region="ewr",
    plan="vc2-1c-2gb",
    os_id=1743,  # Ubuntu 22.04
    label="orchestra-redis",
    vpc_ids=[vpc.id],
    user_data="""
"""
pulumi.export("k8s_cluster_id", k8s_cluster.id)
pulumi.export("postgres_connection", postgres.connection_uri)
pulumi.export("redis_ip", redis.main_ip)
pulumi.export("vpc_id", vpc.id)