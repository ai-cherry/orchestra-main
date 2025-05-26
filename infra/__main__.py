"""
AI Orchestra Infrastructure
===========================
Deploys the complete AI Orchestra stack with managed services
"""

import pulumi
import pulumi_kubernetes as k8s
from pulumi import Config, Output

# Get configuration
config = Config()
project_id = config.require("gcp:project")
region = config.get("gcp:region", "us-central1")
zone = config.get("gcp:zone", f"{region}-a")

# Get managed service credentials from Pulumi config
mongodb_uri = config.require_secret("mongodb_uri")
dragonfly_url = config.require_secret("dragonfly_url")
weaviate_endpoint = config.require_secret("weaviate_endpoint")
weaviate_api_key = config.require_secret("weaviate_api_key")

# Get API keys
openai_api_key = config.get_secret("openai_api_key")
anthropic_api_key = config.get_secret("anthropic_api_key")

# Use existing cluster
cluster_name = "coder-control"
cluster_endpoint = "https://34.171.218.10"

# Create Kubernetes provider for existing cluster
k8s_provider = k8s.Provider(
    "gke-provider",
    kubeconfig=Output.all(project_id, zone, cluster_name).apply(
        lambda args: f"""
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: {cluster_endpoint}
    insecure-skip-tls-verify: true
  name: {args[2]}
contexts:
- context:
    cluster: {args[2]}
    user: {args[2]}
  name: {args[2]}
current-context: {args[2]}
users:
- name: {args[2]}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl
      provideClusterInfo: true
"""
    ),
)

# Create namespace
namespace = k8s.core.v1.Namespace(
    "ai-orchestra-namespace",
    metadata={"name": "ai-orchestra"},
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

# Create secrets for managed services
managed_services_secret = k8s.core.v1.Secret(
    "managed-services",
    metadata={"name": "managed-services", "namespace": "ai-orchestra"},
    string_data={
        "mongodb-uri": mongodb_uri,
        "dragonfly-url": dragonfly_url,
        "weaviate-endpoint": weaviate_endpoint,
        "weaviate-api-key": weaviate_api_key,
        "openai-api-key": openai_api_key or "",
        "anthropic-api-key": anthropic_api_key or "",
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# Deploy AI Orchestra application
deployment = k8s.apps.v1.Deployment(
    "ai-orchestra",
    metadata={
        "name": "ai-orchestra",
        "namespace": "ai-orchestra",
        "labels": {"app": "ai-orchestra"},
    },
    spec={
        "replicas": 2,
        "selector": {"matchLabels": {"app": "ai-orchestra"}},
        "template": {
            "metadata": {"labels": {"app": "ai-orchestra"}},
            "spec": {
                "containers": [
                    {
                        "name": "orchestra",
                        "image": "superagi/superagi:latest",  # Using SuperAGI image
                        "ports": [{"containerPort": 8080}],
                        "env": [
                            {
                                "name": "MONGODB_URI",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "managed-services",
                                        "key": "mongodb-uri",
                                    }
                                },
                            },
                            {
                                "name": "REDIS_URL",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "managed-services",
                                        "key": "dragonfly-url",
                                    }
                                },
                            },
                            {
                                "name": "WEAVIATE_URL",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "managed-services",
                                        "key": "weaviate-endpoint",
                                    }
                                },
                            },
                            {
                                "name": "WEAVIATE_API_KEY",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "managed-services",
                                        "key": "weaviate-api-key",
                                    }
                                },
                            },
                            {"name": "ENVIRONMENT", "value": "production"},
                            {"name": "LOG_LEVEL", "value": "INFO"},
                        ],
                        "resources": {
                            "requests": {"memory": "2Gi", "cpu": "1"},
                            "limits": {"memory": "4Gi", "cpu": "2"},
                        },
                    }
                ]
            },
        },
    },
    opts=pulumi.ResourceOptions(
        provider=k8s_provider, depends_on=[managed_services_secret]
    ),
)

# Create service
service = k8s.core.v1.Service(
    "ai-orchestra-service",
    metadata={
        "name": "ai-orchestra",
        "namespace": "ai-orchestra",
        "labels": {"app": "ai-orchestra"},
    },
    spec={
        "selector": {"app": "ai-orchestra"},
        "ports": [{"port": 8080, "targetPort": 8080, "name": "http"}],
        "type": "LoadBalancer",
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[deployment]),
)

# Export outputs
pulumi.export("namespace", "ai-orchestra")
pulumi.export(
    "service_endpoint",
    service.status.apply(
        lambda status: (
            f"http://{status.load_balancer.ingress[0].ip}:8080"
            if status.load_balancer.ingress
            else "pending"
        )
    ),
)
pulumi.export("cluster_name", cluster_name)
pulumi.export(
    "managed_services",
    {
        "mongodb": "MongoDB Atlas (managed)",
        "dragonfly": "DragonflyDB Cloud (12.5GB)",
        "weaviate": "Weaviate Cloud (managed)",
    },
)
