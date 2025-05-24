"""
Pulumi GCP Infrastructure Stack for Orchestra AI

- Modular, Python-based Pulumi stack for reproducible, high-performance GCP environments.
- Provisions VPC, subnets, IAM, Cloud Run, Redis, AlloyDB, Secret Manager, Artifact Registry, and monitoring.
- Designed for extensibility, automation, and optimal performance.

Author: Orchestra AI Platform
"""

import pulumi
import pulumi_gcp as gcp

# --- CONFIGURATION ---
config = pulumi.Config()
project = config.require("project")
region = config.get("region") or "us-central1"
image_tag = config.get("image_tag") or "latest"
network_name = "orchestra-vpc"
subnet_name = "orchestra-subnet"
service_account_name = "orchestra-sa"
redis_instance_name = "orchestra-redis"
alloydb_instance_name = "orchestra-alloydb"
cloud_run_api_service_name = "ai-orchestra-minimal"
cloud_run_admin_service_name = "admin-interface"
cloud_run_webscraping_service_name = "web-scraping-agents"
artifact_registry_name = "orchestra-repo"

# --- VECTOR DATABASE INTEGRATION: PINECONE & WEAVIATE ---
# Pinecone and Weaviate are managed outside GCP, but can be orchestrated via their SDKs.
# API keys and sensitive data should be stored in GCP Secret Manager and referenced here by secret name.

# Pinecone config (non-secret values from Pulumi config)
pinecone_index_name = config.get("pinecone:index_name") or "orchestra-index"
pinecone_dimension = int(config.get("pinecone:dimension") or 1536)
pinecone_environment = config.get("pinecone:environment") or "us-west1-gcp"
# Pinecone API key should be retrieved from GCP Secret Manager at runtime, not stored in config.

# Weaviate config (non-secret values from Pulumi config)
weaviate_endpoint = config.get("weaviate:endpoint") or "https://weaviate-instance-url"
weaviate_api_key_secret = config.get("weaviate:api_key_secret") or "WEAVIATE_API_KEY"
# Weaviate schema can be managed in code or as a separate config file.

# Example: Export config for downstream use (e.g., application layer or CI/CD)
pulumi.export("pinecone_index_name", pinecone_index_name)
pulumi.export("pinecone_dimension", pinecone_dimension)
pulumi.export("pinecone_environment", pinecone_environment)
pulumi.export("weaviate_endpoint", weaviate_endpoint)
pulumi.export("weaviate_api_key_secret", weaviate_api_key_secret)

# To provision Pinecone/Weaviate resources, use their SDKs in the application layer or as a Pulumi dynamic provider.
# See infra/requirements.txt for required SDKs.
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

# --- ARTIFACT REGISTRY ---
artifact_registry = gcp.artifactregistry.Repository(
    artifact_registry_name,
    repository_id=artifact_registry_name,
    format="DOCKER",
    location=region,
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
# NOTE: Pulumi AlloyDB Instance does not accept 'region' as an argument.
# For a full AlloyDB deployment, you must define a Cluster first, then an Instance.
# This is a placeholder for future configuration.
# alloydb_instance = gcp.alloydb.Instance(
#     alloydb_instance_name,
#     network=network.id,
#     project=project,
# )

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

# --- SECRET MANAGER (WEB SCRAPING API KEYS) ---
# Zenrows API Key
zenrows_secret = gcp.secretmanager.Secret(
    "zenrows-api-key",
    secret_id="ZENROWS_API_KEY",
    replication={"automatic": True},
    project=project,
)

# Apify API Key  
apify_secret = gcp.secretmanager.Secret(
    "apify-api-key", 
    secret_id="APIFY_API_KEY",
    replication={"automatic": True},
    project=project,
)

# PhantomBuster API Key
phantombuster_secret = gcp.secretmanager.Secret(
    "phantombuster-api-key",
    secret_id="PHANTOMBUSTER_API_KEY", 
    replication={"automatic": True},
    project=project,
)

# --- CLOUD RUN SERVICES ---

# Orchestra API Service
orchestra_api_service = gcp.cloudrun.Service(
    cloud_run_api_service_name,
    location=region,
    template={
        "metadata": {
            "annotations": {
                "autoscaling.knative.dev/maxScale": "10",
                "run.googleapis.com/execution-environment": "gen2"
            }
        },
        "spec": {
            "containers": [{
                "image": f"us-central1-docker.pkg.dev/{project}/orchestra-images/orchestra-main:{image_tag}",
                "envs": [
                    {"name": "GOOGLE_CLOUD_PROJECT", "value": project},
                    {"name": "REDIS_HOST", "valueFrom": {"secretKeyRef": {"name": "REDIS_HOST", "key": "latest"}}},
                    {"name": "DRAGONFLY_HOST", "valueFrom": {"secretKeyRef": {"name": "DRAGONFLY_HOST", "key": "latest"}}},
                ],
                "ports": [{"containerPort": 8080}],
                "resources": {
                    "limits": {"cpu": "2", "memory": "4Gi"},
                    "requests": {"cpu": "1", "memory": "2Gi"}
                },
                "startupProbe": {
                    "httpGet": {"path": "/health", "port": 8080},
                    "initialDelaySeconds": 30,
                    "timeoutSeconds": 5
                },
                "livenessProbe": {
                    "httpGet": {"path": "/health", "port": 8080},
                    "periodSeconds": 30
                }
            }],
            "serviceAccountName": service_account.email,
            "containerConcurrency": 80,
        }
    },
    traffics=[{"percent": 100, "latestRevision": True}],
    project=project,
)

# Web Scraping Agents Service
web_scraping_service = gcp.cloudrun.Service(
    cloud_run_webscraping_service_name,
    location=region,
    template={
        "metadata": {
            "annotations": {
                "autoscaling.knative.dev/maxScale": "20",
                "autoscaling.knative.dev/minScale": "1", 
                "run.googleapis.com/execution-environment": "gen2"
            }
        },
        "spec": {
            "containers": [{
                "image": f"us-central1-docker.pkg.dev/{project}/orchestra-images/web-scraping-agents:{image_tag}",
                "envs": [
                    {"name": "GOOGLE_CLOUD_PROJECT", "value": project},
                    {"name": "REDIS_HOST", "valueFrom": {"secretKeyRef": {"name": "REDIS_HOST", "key": "latest"}}},
                    {"name": "REDIS_PORT", "value": "6379"},
                    {"name": "SEARCH_AGENTS", "value": "3"},
                    {"name": "SCRAPER_AGENTS", "value": "5"},
                    {"name": "ANALYZER_AGENTS", "value": "3"},
                    {"name": "ZENROWS_API_KEY", "valueFrom": {"secretKeyRef": {"name": "ZENROWS_API_KEY", "key": "latest"}}},
                    {"name": "APIFY_API_KEY", "valueFrom": {"secretKeyRef": {"name": "APIFY_API_KEY", "key": "latest"}}},
                    {"name": "PHANTOMBUSTER_API_KEY", "valueFrom": {"secretKeyRef": {"name": "PHANTOMBUSTER_API_KEY", "key": "latest"}}},
                    {"name": "OPENAI_API_KEY", "valueFrom": {"secretKeyRef": {"name": "OPENAI_API_KEY", "key": "latest"}}},
                ],
                "ports": [{"containerPort": 8080}],
                "resources": {
                    "limits": {"cpu": "4", "memory": "8Gi"},
                    "requests": {"cpu": "2", "memory": "4Gi"}
                },
                "startupProbe": {
                    "httpGet": {"path": "/health", "port": 8080},
                    "initialDelaySeconds": 60,
                    "timeoutSeconds": 10
                },
                "livenessProbe": {
                    "httpGet": {"path": "/health", "port": 8080},
                    "periodSeconds": 60
                }
            }],
            "serviceAccountName": service_account.email,
            "containerConcurrency": 40,
        }
    },
    traffics=[{"percent": 100, "latestRevision": True}],
    project=project,
)

# Admin Interface Service
admin_interface_service = gcp.cloudrun.Service(
    cloud_run_admin_service_name,
    location=region,
    template={
        "metadata": {
            "annotations": {
                "autoscaling.knative.dev/maxScale": "5",
                "run.googleapis.com/execution-environment": "gen2"
            }
        },
        "spec": {
            "containers": [{
                "image": f"us-central1-docker.pkg.dev/{project}/orchestra-images/admin-interface:{image_tag}",
                "envs": [
                    {"name": "GOOGLE_CLOUD_PROJECT", "value": project},
                ],
                "ports": [{"containerPort": 8080}],
                "resources": {
                    "limits": {"cpu": "2", "memory": "2Gi"},
                    "requests": {"cpu": "1", "memory": "1Gi"}
                },
            }],
            "serviceAccountName": service_account.email,
        }
    },
    traffics=[{"percent": 100, "latestRevision": True}],
    project=project,
)

# --- MONITORING & LOGGING (DASHBOARD EXAMPLE) ---
# monitoring_dashboard = gcp.monitoring.Dashboard(
#     "orchestra-dashboard",
#     dashboard_json=open("monitoring/prometheus.json").read(),
#     project=project,
# )

# --- OUTPUTS ---
pulumi.export("network", network.id)
pulumi.export("subnet", subnet.id)
pulumi.export("service_account", service_account.email)
pulumi.export("redis_instance", redis.id)
# pulumi.export("alloydb_instance", alloydb_instance.id)  # AlloyDB instance not defined
pulumi.export("api_key_secret", api_key_secret.id)
pulumi.export("artifact_registry", artifact_registry.id)
pulumi.export("orchestra_api_url", orchestra_api_service.statuses[0].url)
pulumi.export("admin_interface_url", admin_interface_service.statuses[0].url)
pulumi.export("web_scraping_url", web_scraping_service.statuses[0].url)
pulumi.export("zenrows_secret", zenrows_secret.id)
pulumi.export("apify_secret", apify_secret.id)
pulumi.export("phantombuster_secret", phantombuster_secret.id)
