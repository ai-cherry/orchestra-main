"""
Pulumi GCP Infrastructure Stack for Orchestra AI

- Modular, Python-based Pulumi stack for reproducible, high-performance GCP environments.
- Provisions VPC, subnets, IAM, Cloud Run, Redis, AlloyDB, Secret Manager, and monitoring.
- Designed for extensibility, automation, and optimal performance.

Author: Orchestra AI Platform
"""

import pulumi
import pulumi_gcp as gcp

# --- CONFIGURATION ---
config = pulumi.Config()
project = config.require("project")
region = config.get("region") or "us-central1"
network_name = "orchestra-vpc"
subnet_name = "orchestra-subnet"
service_account_name = "orchestra-sa"
redis_instance_name = "orchestra-redis"
alloydb_instance_name = "orchestra-alloydb"
cloud_run_service_name = "orchestra-api"

# --- VPC & SUBNET ---
network = gcp.compute.Network(
    network_name,
    auto_create_subnetworks=False,
    project=project,
)

subnet = gcp.compute.Subnetwork(
    subnet_name,
    ip_cidr_range="10.10.0.0/16",
    region=region,
    network=network.id,
    project=project,
)

# --- SERVICE ACCOUNT ---
service_account = gcp.serviceaccount.Account(
    service_account_name,
    account_id=service_account_name,
    display_name="Orchestra Service Account",
    project=project,
)

# --- IAM ROLES ---
for role in [
    "roles/owner",
    "roles/secretmanager.admin",
    "roles/redis.admin",
    "roles/alloydb.admin",
    "roles/run.admin",
]:
    gcp.projects.IAMMember(
        f"{service_account_name}-{role}",
        project=project,
        role=role,
        member=service_account.email.apply(lambda email: f"serviceAccount:{email}"),
    )

# --- REDIS (MEMORYSTORE) ---
redis = gcp.redis.Instance(
    redis_instance_name,
    tier="STANDARD_HA",
    memory_size_gb=4,
    region=region,
    authorized_network=network.id,
    project=project,
)

# --- ALLOYDB ---
alloydb_instance = gcp.alloydb.Instance(
    alloydb_instance_name,
    region=region,
    network=network.id,
    project=project,
)

# --- SECRET MANAGER (EXAMPLE SECRET) ---
api_key_secret = gcp.secretmanager.Secret(
    "orchestra-api-key",
    replication={"automatic": True},
    project=project,
)
api_key_secret_version = gcp.secretmanager.SecretVersion(
    "orchestra-api-key-version",
    secret=api_key_secret.id,
    secret_data="your-api-key-value",
    project=project,
)

# --- CLOUD RUN SERVICE (PLACEHOLDER) ---
# To deploy an image, uncomment and set image URL
# cloud_run_service = gcp.cloudrun.Service(
#     cloud_run_service_name,
#     location=region,
#     template={
#         "spec": {
#             "containers": [{
#                 "image": "gcr.io/<project>/orchestra-api:latest",
#                 "envs": [],
#             }],
#             "serviceAccountName": service_account.email,
#         }
#     },
#     traffics=[{"percent": 100, "latestRevision": True}],
#     project=project,
# )

# --- MONITORING & LOGGING (DASHBOARD EXAMPLE) ---
# monitoring_dashboard = gcp.monitoring.Dashboard(
#     "orchestra-dashboard",
#     dashboard_json=open("monitoring/prometheus.json").read(),
#     project=project,
# )

pulumi.export("network", network.id)
pulumi.export("subnet", subnet.id)
pulumi.export("service_account", service_account.email)
pulumi.export("redis_instance", redis.id)
pulumi.export("alloydb_instance", alloydb_instance.id)
pulumi.export("api_key_secret", api_key_secret.id)
