"""
Main Pulumi Infrastructure Orchestration
========================================
Modular infrastructure deployment for AI Orchestra with SuperAGI
"""

import pulumi
from pulumi import Config, ResourceOptions
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s

# Import modular components
from components.database_component import DatabaseComponent
from components.superagi_component import SuperAGIComponent
from components.weaviate_component import WeaviateComponent
from components.monitoring_component import MonitoringComponent
from components.litellm_component import LiteLLMComponent

# Get configuration
config = Config()
project_id = config.require("gcp_project_id")
region = config.get("region", "us-central1")
zone = config.get("zone", f"{region}-a")
environment = pulumi.get_stack()

# Common tags
common_tags = {
    "project": "ai-orchestra",
    "environment": environment,
    "managed-by": "pulumi",
}

# Enable required GCP APIs
apis = [
    "container.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
]

enabled_apis = []
for api in apis:
    enabled_api = gcp.projects.Service(
        f"enable-{api.replace('.', '-')}",
        service=api,
        project=project_id,
        disable_on_destroy=False,
    )
    enabled_apis.append(enabled_api)

# Create GKE cluster
cluster = gcp.container.Cluster(
    f"orchestra-cluster-{environment}",
    name=f"orchestra-cluster-{environment}",
    location=zone,
    initial_node_count=1,
    remove_default_node_pool=True,
    min_master_version="latest",
    resource_labels=common_tags,
    workload_identity_config=gcp.container.ClusterWorkloadIdentityConfigArgs(
        workload_pool=f"{project_id}.svc.id.goog",
    ),
    opts=ResourceOptions(depends_on=enabled_apis),
)

# Create node pool
node_pool = gcp.container.NodePool(
    f"orchestra-node-pool-{environment}",
    name=f"orchestra-node-pool-{environment}",
    cluster=cluster.name,
    location=zone,
    initial_node_count=2,
    autoscaling=gcp.container.NodePoolAutoscalingArgs(
        min_node_count=2,
        max_node_count=10,
    ),
    node_config=gcp.container.NodePoolNodeConfigArgs(
        machine_type="n2-standard-4",
        disk_size_gb=100,
        disk_type="pd-ssd",
        oauth_scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
        ],
        workload_metadata_config=gcp.container.NodePoolNodeConfigWorkloadMetadataConfigArgs(
            mode="GKE_METADATA",
        ),
        labels=common_tags,
    ),
    management=gcp.container.NodePoolManagementArgs(
        auto_repair=True,
        auto_upgrade=True,
    ),
)

# Create Kubernetes provider
k8s_provider = k8s.Provider(
    "k8s-provider",
    kubeconfig=pulumi.Output.all(
        cluster.name, cluster.endpoint, cluster.master_auth
    ).apply(
        lambda args: f"""
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {args[2].cluster_ca_certificate}
    server: https://{args[1]}
  name: {args[0]}
contexts:
- context:
    cluster: {args[0]}
    user: {args[0]}
  name: {args[0]}
current-context: {args[0]}
kind: Config
preferences: {{}}
users:
- name: {args[0]}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gcloud
      args:
      - container
      - clusters
      - get-credentials
      - {args[0]}
      - --zone={zone}
      - --project={project_id}
"""
    ),
    opts=ResourceOptions(depends_on=[cluster, node_pool]),
)

# Create namespace
namespace = k8s.core.v1.Namespace(
    "superagi-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi",
        labels=common_tags,
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Deploy LiteLLM gateway for unified LLM access
litellm_api_keys = {
    "OPENAI_API_KEY": config.require_secret("openai_api_key"),
    "ANTHROPIC_API_KEY": config.get_secret("anthropic_api_key"),
    "HUGGINGFACE_API_KEY": config.get_secret("huggingface_api_key"),
}
litellm_component = LiteLLMComponent(
    "orchestra-litellm",
    config={
        "namespace": "superagi",
        "image": "berriai/litellm:latest",
        "replicas": 1,
        "api_keys": litellm_api_keys,
        "port": 4000,
    },
    opts=ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# Create service account for SuperAGI
service_account = gcp.serviceaccount.Account(
    f"superagi-sa-{environment}",
    account_id=f"superagi-sa-{environment}",
    display_name="SuperAGI Service Account",
    project=project_id,
)

# Grant necessary permissions
firestore_binding = gcp.projects.IAMMember(
    "superagi-firestore-access",
    project=project_id,
    role="roles/datastore.user",
    member=f"serviceAccount:{service_account.email}",
)

storage_binding = gcp.projects.IAMMember(
    "superagi-storage-access",
    project=project_id,
    role="roles/storage.objectAdmin",
    member=f"serviceAccount:{service_account.email}",
)

# Create Workload Identity binding
workload_identity_binding = gcp.serviceaccount.IAMBinding(
    "superagi-workload-identity",
    service_account_id=service_account.name,
    role="roles/iam.workloadIdentityUser",
    members=[f"serviceAccount:{project_id}.svc.id.goog[superagi/superagi-sa]"],
)

# Create Kubernetes service account
k8s_service_account = k8s.core.v1.ServiceAccount(
    "superagi-k8s-sa",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi-sa",
        namespace=namespace.metadata.name,
        annotations={
            "iam.gke.io/gcp-service-account": service_account.email,
        },
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Deploy database components
database_config = {
    "namespace": "superagi",
    "project_id": project_id,
    "dragonfly_storage": "20Gi",
    "dragonfly_max_memory": "8Gi",
    "enable_mongodb": True,
    "mongodb_storage": "100Gi",
}

database_component = DatabaseComponent(
    "orchestra-databases",
    config=database_config,
    opts=ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# Deploy Weaviate vector DB
weaviate_config = {
    "namespace": "superagi",
    "weaviate_api_key": config.require_secret("weaviate_api_key"),
    "weaviate_rest_endpoint": config.require("weaviate_rest_endpoint"),
    "replicas": 1,
    "storage": "50Gi",
}
weaviate_component = WeaviateComponent(
    "orchestra-weaviate",
    config=weaviate_config,
    opts=ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# Deploy SuperAGI with MCP integration
superagi_config = {
    "namespace": "superagi",
    "project_id": project_id,
    "replicas": 3,
    "max_concurrent_agents": 20,
    "enable_mongodb_mcp": True,
    "enable_weaviate_mcp": True,
    # Use the actual Weaviate endpoint from the provisioned component
    "weaviate_url": weaviate_component.outputs["endpoint"],
    # Use LiteLLM as the OpenAI-compatible LLM gateway
    "llm_gateway_url": litellm_component.outputs["endpoint"],
}

superagi_component = SuperAGIComponent(
    "orchestra-superagi",
    config=superagi_config,
    database_outputs={
        "dragonfly_host": database_component.dragonfly["host"],
        "dragonfly_port": database_component.dragonfly["port"],
        "mongodb_uri": (
            database_component.mongodb.get("uri")
            if hasattr(database_component, "mongodb")
            else None
        ),
    },
    opts=ResourceOptions(provider=k8s_provider, depends_on=[database_component]),
)

# Deploy monitoring stack
monitoring_component = MonitoringComponent(
    "orchestra-monitoring",
    namespace="monitoring",
    storage_class="standard",
    grafana_admin_password=config.get_secret("grafana_admin_password"),
    opts=ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
)

# Deploy ingress with domain configuration
from components.ingress_component import IngressComponent

ingress_config = {
    "namespace": "superagi",
    "domain": "cherry-ai.me",
}

ingress_component = IngressComponent(
    "orchestra-ingress",
    config=ingress_config,
    service_name="superagi",
    opts=ResourceOptions(provider=k8s_provider, depends_on=[superagi_component]),
)

# Export important values
pulumi.export("cluster_name", cluster.name)
pulumi.export("cluster_endpoint", cluster.endpoint)
pulumi.export("namespace", namespace.metadata.name)
pulumi.export(
    "superagi_endpoint", superagi_component.service.status.load_balancer.ingress[0].ip
)
pulumi.export(
    "mcp_mongodb_endpoint", superagi_component.mcp_servers["mongodb"]["endpoint"]
)
pulumi.export(
    "mcp_weaviate_endpoint", superagi_component.mcp_servers["weaviate"]["endpoint"]
)
pulumi.export("service_account_email", service_account.email)
pulumi.export("domain", "cherry-ai.me")
pulumi.export("https_endpoint", "https://cherry-ai.me")
pulumi.export("prometheus_endpoint", monitoring_component.prometheus_endpoint)
pulumi.export("grafana_endpoint", monitoring_component.grafana_endpoint)

# Stack outputs for cross-stack references
pulumi.export(
    "stack_outputs",
    {
        "cluster": {
            "name": cluster.name,
            "endpoint": cluster.endpoint,
            "location": cluster.location,
        },
        "database": {
            "dragonfly_host": database_component.dragonfly["host"],
            "mongodb_uri": (
                database_component.mongodb.get("uri")
                if hasattr(database_component, "mongodb")
                else None
            ),
        },
        "superagi": {
            "endpoint": superagi_component.service.status.load_balancer.ingress[0].ip,
            "mcp_endpoints": {
                "mongodb": superagi_component.mcp_servers["mongodb"]["endpoint"],
                "weaviate": superagi_component.mcp_servers["weaviate"]["endpoint"],
            },
        },
    },
)
