"""
Weaviate Component for Pulumi Infrastructure
===========================================
Provisions a Weaviate vector database instance in Kubernetes, with all credentials and endpoints managed via Pulumi secrets and injected as Kubernetes Secrets.

Usage:
    from .weaviate_component import WeaviateComponent

    weaviate = WeaviateComponent(
        name="orchestra-weaviate",
        config={
            "namespace": "superagi",
            "weaviate_api_key": "...",  # Pulumi config key
            "weaviate_rest_endpoint": "...",  # Pulumi config key
            "replicas": 1,
            "storage": "50Gi",
        },
        opts=ResourceOptions(...)
    )
"""

from typing import Any, Dict, Optional

import pulumi_kubernetes as k8s
from pulumi import ComponentResource, ResourceOptions

from .secret_helper import create_k8s_secret_from_config


class WeaviateComponent(ComponentResource):
    """
    Reusable Weaviate deployment component for the AI Orchestra system.
    Provisions Weaviate as a Kubernetes Deployment + Service, with secrets managed via Pulumi config.
    """

    def __init__(self, name: str, config: Dict[str, Any], opts: Optional[ResourceOptions] = None):
        super().__init__("orchestra:weaviate:Component", name, None, opts)

        self.config = config
        self.namespace = config.get("namespace", "superagi")

        # Create Kubernetes Secret for Weaviate API key and endpoint
        self.weaviate_secret = create_k8s_secret_from_config(
            name="weaviate-secrets",
            namespace=self.namespace,
            keys=["weaviate-api-key", "weaviate-rest-endpoint"],
            config_prefix="",
            opts=opts,
        )

        # Persistent Volume Claim for Weaviate data
        pvc = k8s.core.v1.PersistentVolumeClaim(
            f"{name}-weaviate-pvc",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="weaviate-data",
                namespace=self.namespace,
            ),
            spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
                access_modes=["ReadWriteOnce"],
                storage_class_name="pd-ssd",
                resources=k8s.core.v1.ResourceRequirementsArgs(
                    requests={"storage": config.get("storage", "50Gi")},
                ),
            ),
            opts=opts,
        )

        # Weaviate Deployment
        deployment = k8s.apps.v1.Deployment(
            f"{name}-weaviate",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="weaviate",
                namespace=self.namespace,
                labels={"app": "weaviate"},
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=config.get("replicas", 1),
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels={"app": "weaviate"},
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels={"app": "weaviate"},
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name="weaviate",
                                image="semitechnologies/weaviate:1.24.7",
                                ports=[k8s.core.v1.ContainerPortArgs(container_port=8080)],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name="WEAVIATE_API_KEY",
                                        value_from=k8s.core.v1.EnvVarSourceArgs(
                                            secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                                                name="weaviate-secrets",
                                                key="weaviate-api-key",
                                            ),
                                        ),
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name="WEAVIATE_HOST",
                                        value_from=k8s.core.v1.EnvVarSourceArgs(
                                            secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                                                name="weaviate-secrets",
                                                key="weaviate-rest-endpoint",
                                            ),
                                        ),
                                    ),
                                ],
                                volume_mounts=[
                                    k8s.core.v1.VolumeMountArgs(
                                        name="data",
                                        mount_path="/var/lib/weaviate",
                                    ),
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={"memory": "2Gi", "cpu": "1"},
                                    limits={"memory": "4Gi", "cpu": "2"},
                                ),
                                liveness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/v1/.well-known/ready",
                                        port=8080,
                                    ),
                                    initial_delay_seconds=30,
                                    period_seconds=10,
                                ),
                                readiness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/v1/.well-known/ready",
                                        port=8080,
                                    ),
                                    initial_delay_seconds=10,
                                    period_seconds=5,
                                ),
                            )
                        ],
                        volumes=[
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
            opts=opts,
        )

        # Weaviate Service
        service = k8s.core.v1.Service(
            f"{name}-weaviate-service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="weaviate",
                namespace=self.namespace,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                selector={"app": "weaviate"},
                ports=[k8s.core.v1.ServicePortArgs(port=8080, target_port=8080)],
                type="ClusterIP",
            ),
            opts=opts,
        )

        # Export endpoint for use by MCP and other components
        self.register_outputs(
            {
                "service": service,
                "deployment": deployment,
                "endpoint": service.metadata.name.apply(lambda n: f"http://{n}:8080"),
            }
        )
