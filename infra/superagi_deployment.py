"""
SuperAGI Deployment Stack for Orchestra AI
==========================================
This Pulumi stack deploys SuperAGI on GKE (Google Kubernetes Engine) with:
- GKE cluster with autoscaling
- SuperAGI deployment with persistent storage
- Integration with existing Orchestra components
- DragonflyDB for short-term memory
- Cloud SQL for long-term storage
"""

import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
from pulumi import Config, Output, ResourceOptions

# Configuration
config = Config()
project_id = config.require("gcp:project")
region = config.get("gcp:region") or "us-central1"
zone = f"{region}-a"

# Reference existing resources from main stack
orchestra_stack = pulumi.StackReference("orchestra-main")
service_account_email = orchestra_stack.get_output("service_account_email")

# Create GKE cluster for SuperAGI
cluster = gcp.container.Cluster(
    "superagi-cluster",
    name="superagi-cluster",
    location=zone,
    initial_node_count=1,
    remove_default_node_pool=True,
    min_master_version="1.27",
    network="default",
    subnetwork="default",
    master_auth=gcp.container.ClusterMasterAuthArgs(
        client_certificate_config=gcp.container.ClusterMasterAuthClientCertificateConfigArgs(
            issue_client_certificate=False,
        ),
    ),
    workload_identity_config=gcp.container.ClusterWorkloadIdentityConfigArgs(
        workload_pool=f"{project_id}.svc.id.goog",
    ),
)

# Create node pool with autoscaling
node_pool = gcp.container.NodePool(
    "superagi-node-pool",
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
        service_account=service_account_email,
        workload_metadata_config=gcp.container.NodePoolNodeConfigWorkloadMetadataConfigArgs(
            mode="GKE_METADATA",
        ),
    ),
    management=gcp.container.NodePoolManagementArgs(
        auto_repair=True,
        auto_upgrade=True,
    ),
)

# Create Kubernetes provider
k8s_provider = k8s.Provider(
    "k8s-provider",
    kubeconfig=Output.all(cluster.name, cluster.endpoint, cluster.master_auth).apply(
        lambda args: f"""apiVersion: v1
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

# Create namespace for SuperAGI
namespace = k8s.core.v1.Namespace(
    "superagi-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi",
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Create PersistentVolumeClaim for SuperAGI data
pvc = k8s.core.v1.PersistentVolumeClaim(
    "superagi-data-pvc",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi-data",
        namespace=namespace.metadata.name,
    ),
    spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
        access_modes=["ReadWriteOnce"],
        storage_class_name="pd-ssd",
        resources=k8s.core.v1.ResourceRequirementsArgs(
            requests={"storage": "50Gi"},
        ),
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Deploy DragonflyDB for short-term memory
dragonfly_deployment = k8s.apps.v1.Deployment(
    "dragonfly-deployment",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="dragonfly",
        namespace=namespace.metadata.name,
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={"app": "dragonfly"},
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={"app": "dragonfly"},
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="dragonfly",
                        image="docker.dragonflydb.io/dragonflydb/dragonfly:latest",
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=6379)],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            requests={
                                "memory": "2Gi",
                                "cpu": "1",
                            },
                            limits={
                                "memory": "4Gi",
                                "cpu": "2",
                            },
                        ),
                    )
                ],
            ),
        ),
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# DragonflyDB Service
dragonfly_service = k8s.core.v1.Service(
    "dragonfly-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="dragonfly",
        namespace=namespace.metadata.name,
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        selector={"app": "dragonfly"},
        ports=[k8s.core.v1.ServicePortArgs(port=6379, target_port=6379)],
        type="ClusterIP",
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Create ConfigMap for SuperAGI configuration
superagi_config = k8s.core.v1.ConfigMap(
    "superagi-config",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi-config",
        namespace=namespace.metadata.name,
    ),
    data={
        "config.yaml": """
# SuperAGI Configuration
redis:
  host: dragonfly
  port: 6379

agents:
  max_concurrent: 10
  timeout: 300

memory:
  short_term:
    provider: redis
    ttl: 3600
  long_term:
    provider: firestore

integration:
  orchestra_api: http://orchestra-api:8080
  mcp_server: http://mcp-server:8080
""",
    },
    opts=ResourceOptions(provider=k8s_provider),
)

# Deploy SuperAGI
superagi_deployment = k8s.apps.v1.Deployment(
    "superagi-deployment",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi",
        namespace=namespace.metadata.name,
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=2,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={"app": "superagi"},
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={"app": "superagi"},
            ),
            spec=k8s.core.v1.PodSpecArgs(
                service_account_name="superagi-sa",
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name="superagi",
                        image="gcr.io/{}/superagi:latest".format(project_id),
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=8080)],
                        env=[
                            k8s.core.v1.EnvVarArgs(
                                name="REDIS_HOST",
                                value="dragonfly",
                            ),
                            k8s.core.v1.EnvVarArgs(
                                name="REDIS_PORT",
                                value="6379",
                            ),
                            k8s.core.v1.EnvVarArgs(
                                name="GCP_PROJECT_ID",
                                value=project_id,
                            ),
                            k8s.core.v1.EnvVarArgs(
                                name="OPENROUTER_API_KEY",
                                value_from=k8s.core.v1.EnvVarSourceArgs(
                                    secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                                        name="superagi-secrets",
                                        key="openrouter-api-key",
                                    ),
                                ),
                            ),
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name="config",
                                mount_path="/app/config",
                            ),
                            k8s.core.v1.VolumeMountArgs(
                                name="data",
                                mount_path="/app/data",
                            ),
                        ],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            requests={
                                "memory": "2Gi",
                                "cpu": "1",
                            },
                            limits={
                                "memory": "4Gi",
                                "cpu": "2",
                            },
                        ),
                        liveness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path="/health",
                                port=8080,
                            ),
                            initial_delay_seconds=30,
                            period_seconds=10,
                        ),
                        readiness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path="/ready",
                                port=8080,
                            ),
                            initial_delay_seconds=10,
                            period_seconds=5,
                        ),
                    )
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name="config",
                        config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
                            name=superagi_config.metadata.name,
                        ),
                    ),
                    k8s.core.v1.VolumeArgs(
                        name="data",
                        persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                            claim_name=pvc.metadata.name,
                        ),
                    ),
                ],
            ),
        ),
    ),
    opts=ResourceOptions(provider=k8s_provider, depends_on=[dragonfly_service]),
)

# SuperAGI Service
superagi_service = k8s.core.v1.Service(
    "superagi-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi",
        namespace=namespace.metadata.name,
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        selector={"app": "superagi"},
        ports=[k8s.core.v1.ServicePortArgs(port=8080, target_port=8080)],
        type="LoadBalancer",
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Create Kubernetes Service Account for SuperAGI
k8s_service_account = k8s.core.v1.ServiceAccount(
    "superagi-sa",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="superagi-sa",
        namespace=namespace.metadata.name,
        annotations={
            "iam.gke.io/gcp-service-account": service_account_email,
        },
    ),
    opts=ResourceOptions(provider=k8s_provider),
)

# Bind GCP service account to Kubernetes service account
workload_identity_binding = gcp.serviceaccount.IAMBinding(
    "superagi-workload-identity",
    service_account_id=service_account_email.apply(
        lambda email: f"projects/{project_id}/serviceAccounts/{email}"
    ),
    role="roles/iam.workloadIdentityUser",
    members=[
        f"serviceAccount:{project_id}.svc.id.goog[superagi/superagi-sa]",
    ],
)

# Outputs
pulumi.export("cluster_name", cluster.name)
pulumi.export("cluster_endpoint", cluster.endpoint)
pulumi.export(
    "superagi_service_ip", superagi_service.status.load_balancer.ingress[0].ip
)
pulumi.export("namespace", namespace.metadata.name)
