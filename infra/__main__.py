"""
Pulumi infrastructure for Orchestra AI on Vultr.
"""
import pulumi
import pulumi_vultr as vultr
from pulumi import Config, Output

# Get configuration
config = Config()
environment = pulumi.get_stack()
region = config.require("vultr:region")

# Create a VPC
vpc = vultr.Vpc("orchestra-vpc",
    region=region,
    description=f"Orchestra AI VPC - {environment}",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create a Kubernetes cluster
k8s_cluster = vultr.Kubernetes("orchestra-k8s",
    region=region,
    label=f"orchestra-{environment}",
    version="v1.28.2",
    node_pools=[{
        "node_quantity": 3,
        "plan": "vc2-4c-8gb",
        "label": "worker-pool",
        "auto_scaler": True,
        "min_nodes": 2,
        "max_nodes": 10
    }]
)

# Create PostgreSQL database
postgres = vultr.Database("orchestra-postgres",
    database_engine="pg",
    database_engine_version="15",
    region=region,
    plan="vultr-dbaas-startup-cc-1-55-2",
    label=f"orchestra-postgres-{environment}"
)

# Export outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("k8s_endpoint", k8s_cluster.endpoint)
pulumi.export("postgres_uri", postgres.connection_uri)
